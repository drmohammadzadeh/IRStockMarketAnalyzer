<?php
declare(strict_types=1);

/**
 * Backend API Endpoint: Insert Stock Analysis Requests into MariaDB
 * Database: tjbir_bourse
 * Server Environment: PHP 8.1+ / MariaDB 10.11+
 * Website: tjb24.ir
 */

// Set JSON and CORS headers
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept, X-Requested-With');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode([
        'success' => false,
        'message' => 'متد ارسالی نامعتبر است. فقط درخواست‌های POST پذیرفته می‌شوند.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Database Configuration
$dbConfig = [
    'host'     => 'localhost',
    'dbname'   => 'tjbir_bourse',
    'username' => 'tjbir_bourse_db_user',
    'password' => '8r0XWGxJI3gOr&?3',
    'charset'  => 'utf8mb4'
];

// SMTP Email Configuration for Internal Notification Dispatch
$smtpConfig = [
    'host'     => 'mail.tjb24.ir',
    'port'     => 465,
    'username' => 'tahlilreq@tjb24.ir',
    'password' => 'Tjb24$$1234',
    'from'     => 'tahlilreq@tjb24.ir',
    'to'       => 'tahlilreq@tjb24.ir',
    'timeout'  => 10
];

/**
 * Robust Client IP Extraction Function
 * Supports Cloudflare, Reverse Proxy, Load Balancers & Direct connections
 */
function getClientIp(): string {
    $headers = [
        'HTTP_CF_CONNECTING_IP', // Cloudflare
        'HTTP_CLIENT_IP',
        'HTTP_X_FORWARDED_FOR',  // Proxy / Load Balancer
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'            // Direct IP
    ];

    foreach ($headers as $header) {
        if (!empty($_SERVER[$header])) {
            $ips = explode(',', (string)$_SERVER[$header]);
            foreach ($ips as $ip) {
                $trimmedIp = trim($ip);
                if (filter_var($trimmedIp, FILTER_VALIDATE_IP)) {
                    return $trimmedIp;
                }
            }
        }
    }

    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

/**
 * Generic SMTP mail sender over SSL (Port 465).
 * Native pure PHP 8.1+ socket implementation with zero external dependencies.
 *
 * @param array<string, mixed> $config  SMTP credentials and server settings
 * @param string               $to      Recipient email address
 * @param string               $subject Email subject (UTF-8)
 * @param string               $htmlBody HTML email content (UTF-8)
 * @param string|null          $replyTo Optional Reply-To address
 * @return bool
 */
function sendSmtpMail(array $config, string $to, string $subject, string $htmlBody, ?string $replyTo = null): bool {
    $host     = (string)$config['host'];
    $port     = (int)$config['port'];
    $timeout  = (int)($config['timeout'] ?? 10);
    $username = (string)$config['username'];
    $password = (string)$config['password'];
    $from     = (string)$config['from'];

    $context = stream_context_create([
        'ssl' => [
            'verify_peer'       => false,
            'verify_peer_name'  => false,
            'allow_self_signed' => true,
        ]
    ]);

    $remote = sprintf('ssl://%s:%d', $host, $port);
    $socket = @stream_socket_client($remote, $errno, $errstr, $timeout, STREAM_CLIENT_CONNECT, $context);
    if (!$socket) {
        throw new RuntimeException("SMTP Connection failed: {$errstr} ({$errno})");
    }

    stream_set_timeout($socket, $timeout);

    $readResponse = function() use ($socket): string {
        $response = '';
        while (!feof($socket)) {
            $line = fgets($socket, 2048);
            if ($line === false) {
                break;
            }
            $response .= $line;
            if (strlen($line) >= 3 && ctype_digit(substr($line, 0, 3))) {
                if (strlen($line) === 3 || $line[3] === ' ' || $line[3] === "\r" || $line[3] === "\n") {
                    break;
                }
            }
        }
        return $response;
    };

    $sendCommand = function(string $cmd, array $expectedCodes) use ($socket, $readResponse): string {
        if ($cmd !== '') {
            fwrite($socket, $cmd . "\r\n");
        }
        $res = $readResponse();
        $code = (int)substr($res, 0, 3);
        if (!in_array($code, $expectedCodes, true)) {
            throw new RuntimeException("SMTP Command [{$cmd}] failed with response: {$res}");
        }
        return $res;
    };

    try {
        $sendCommand('', [220]);
        $sendCommand('EHLO tjb24.ir', [250]);
        $sendCommand('AUTH LOGIN', [334]);
        $sendCommand(base64_encode($username), [334]);
        $sendCommand(base64_encode($password), [235]);
        $sendCommand(sprintf('MAIL FROM:<%s>', $from), [250]);
        $sendCommand(sprintf('RCPT TO:<%s>', $to), [250, 251]);
        $sendCommand('DATA', [354]);

        $encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
        $messageId = sprintf('<%s.%s@tjb24.ir>', uniqid((string)time(), true), bin2hex(random_bytes(4)));

        $headers = [
            'From: "سامانه تحلیل بازار tjb24.ir" <' . $from . '>',
            'To: <' . $to . '>',
            'Date: ' . date(DATE_RFC2822),
            'Subject: ' . $encodedSubject,
            'Message-ID: ' . $messageId,
            'MIME-Version: 1.0',
            'Content-Type: text/html; charset=UTF-8',
            'Content-Transfer-Encoding: base64',
            'X-Mailer: TJB24 Stock Analyzer System'
        ];

        if (!empty($replyTo)) {
            $headers[] = 'Reply-To: <' . $replyTo . '>';
        }

        $encodedBody = chunk_split(base64_encode($htmlBody));
        $fullPayload = implode("\r\n", $headers) . "\r\n\r\n" . $encodedBody . "\r\n.";

        $sendCommand($fullPayload, [250]);

        try {
            $sendCommand('QUIT', [221]);
        } catch (Throwable $ignore) {
        }

        return true;
    } finally {
        if (is_resource($socket)) {
            fclose($socket);
        }
    }
}

/**
 * Build HTML email body for internal notification sent to tahlilreq@tjb24.ir
 */
function buildAdminNotificationHtml(array $data): string {
    $requestId   = (int)($data['request_id'] ?? 0);
    $stockSymbol = htmlspecialchars((string)($data['stock_symbol'] ?? ''), ENT_QUOTES, 'UTF-8');
    $requestType = htmlspecialchars((string)($data['request_type'] ?? ''), ENT_QUOTES, 'UTF-8');
    $name        = htmlspecialchars((string)($data['applicant_name'] ?? ''), ENT_QUOTES, 'UTF-8');
    $email       = htmlspecialchars((string)($data['applicant_email'] ?? ''), ENT_QUOTES, 'UTF-8');
    $ip          = htmlspecialchars((string)($data['ip_address'] ?? ''), ENT_QUOTES, 'UTF-8');
    $ua          = htmlspecialchars((string)($data['user_agent'] ?? ''), ENT_QUOTES, 'UTF-8');
    $referer     = htmlspecialchars((string)($data['referer'] ?? ''), ENT_QUOTES, 'UTF-8');
    $createdAt   = htmlspecialchars((string)($data['created_at'] ?? ''), ENT_QUOTES, 'UTF-8');

    $notesFormatted = !empty($data['notes'])
        ? nl2br(htmlspecialchars((string)$data['notes'], ENT_QUOTES, 'UTF-8'))
        : '<span style="color:#94a3b8;">(بدون توضیحات)</span>';

    $deviceInfoFormatted = htmlspecialchars(
        json_encode($data['extended_device_info'] ?? [], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
        ENT_QUOTES,
        'UTF-8'
    );

    return <<<HTML
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>درخواست تحلیل سهم</title>
</head>
<body dir="rtl" style="margin: 0; padding: 20px; background-color: #f8fafc; font-family: Tahoma, 'Segoe UI', 'Vazirmatn', Arial, sans-serif; direction: rtl; text-align: right; color: #1e293b;">
    <table width="100%" border="0" cellpadding="0" cellspacing="0" dir="rtl" style="background-color: #f8fafc; direction: rtl; text-align: right;">
        <tr>
            <td align="center" dir="rtl" style="direction: rtl; text-align: right;">
                <table width="650" border="0" cellpadding="0" cellspacing="0" dir="rtl" style="max-width: 650px; width: 100%; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; direction: rtl; text-align: right; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07);">
                    <!-- Header -->
                    <tr>
                        <td dir="rtl" style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px 24px; direction: rtl; text-align: right;">
                            <h2 dir="rtl" style="margin: 0 0 6px 0; font-size: 19px; color: #38bdf8; font-family: Tahoma, 'Segoe UI', Arial, sans-serif; direction: rtl; text-align: right;">سامانه تحلیل بازار سرمایه (tjb24.ir)</h2>
                            <p dir="rtl" style="margin: 0; font-size: 13px; color: #94a3b8; direction: rtl; text-align: right;">نسخه کپی از اطلاعات درخواست ثبت‌شده در سامانه</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td dir="rtl" style="padding: 24px; direction: rtl; text-align: right;">
                            <table width="100%" border="0" cellpadding="10" cellspacing="0" dir="rtl" style="width: 100%; border-collapse: collapse; font-size: 14px; direction: rtl; text-align: right; font-family: Tahoma, 'Segoe UI', Arial, sans-serif;">
                                <tr>
                                    <th width="35%" dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">شناسه درخواست:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><strong>#{$requestId}</strong></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">نماد / نام سهم:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><span style="display: inline-block; padding: 4px 10px; font-size: 13px; font-weight: bold; border-radius: 6px; background-color: #e0f2fe; color: #0369a1;">{$stockSymbol}</span></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">نوع درخواست:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><strong>{$requestType}</strong></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">نام متقاضی:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;">{$name}</td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">ایمیل متقاضی:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><a href="mailto:{$email}" style="color: #2563eb; text-decoration: none;">{$email}</a></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">توضیحات تکمیلی:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;">{$notesFormatted}</td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">آدرس IP کاربر:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><code style="background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace;">{$ip}</code></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">مرورگر / سیستم‌عامل:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><small>{$ua}</small></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">صفحه ارجاع‌دهنده:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;"><small>{$referer}</small></td>
                                </tr>
                                <tr>
                                    <th dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #64748b; font-weight: 600; text-align: right; background-color: #f8fafc; direction: rtl;">تاریخ و زمان ثبت:</th>
                                    <td dir="rtl" style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; text-align: right; direction: rtl;">{$createdAt}</td>
                                </tr>
                            </table>
                            <div dir="rtl" style="margin-top: 18px; direction: rtl; text-align: right;">
                                <div dir="rtl" style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 4px; direction: rtl; text-align: right;">جزئیات تلمتری دستگاه (Device Telemetry):</div>
                                <pre dir="ltr" style="background-color: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 11px; direction: ltr; text-align: left; overflow-x: auto; font-family: monospace;">{$deviceInfoFormatted}</pre>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td dir="rtl" style="background-color: #f8fafc; padding: 14px 24px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center; direction: rtl; font-family: Tahoma, 'Segoe UI', Arial, sans-serif;">
                            ارائه‌دهنده و توسعه‌دهنده: <a href="https://tjb24.ir" style="color: #0284c7; text-decoration: none; font-weight: bold;" target="_blank">tjb24.ir</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
HTML;
}

/**
 * Build HTML email body for urgent analysis payment instructions sent to the applicant
 */
function buildApplicantPaymentInstructionHtml(string $applicantName, string $stockSymbol): string {
    $safeName   = htmlspecialchars($applicantName, ENT_QUOTES, 'UTF-8');
    $safeSymbol = htmlspecialchars($stockSymbol, ENT_QUOTES, 'UTF-8');

    return <<<HTML
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>دستورالعمل واریز جهت تحلیل فوری</title>
</head>
<body dir="rtl" style="margin: 0; padding: 25px; background-color: #f8fafc; font-family: Tahoma, 'Segoe UI', 'Vazirmatn', Arial, sans-serif; direction: rtl; text-align: right; color: #1e293b; line-height: 1.9;">
    <!-- Container Table for bulletproof email client RTL rendering -->
    <table width="100%" border="0" cellpadding="0" cellspacing="0" dir="rtl" style="background-color: #f8fafc; direction: rtl; text-align: right;">
        <tr>
            <td align="center" dir="rtl" style="direction: rtl; text-align: right;">
                <table width="600" border="0" cellpadding="0" cellspacing="0" dir="rtl" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; direction: rtl; text-align: right; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07);">
                    <!-- Header -->
                    <tr>
                        <td dir="rtl" style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 22px 26px; direction: rtl; text-align: right;">
                            <h2 dir="rtl" style="margin: 0; font-size: 19px; color: #38bdf8; font-family: Tahoma, 'Segoe UI', Arial, sans-serif; direction: rtl; text-align: right;">سامانه تحلیل بازار سرمایه (tjb24.ir)</h2>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td dir="rtl" style="padding: 28px 26px; font-size: 15px; color: #334155; direction: rtl; text-align: right; font-family: Tahoma, 'Segoe UI', Arial, sans-serif; line-height: 2.0;">
                            <p dir="rtl" style="margin: 0 0 14px 0; direction: rtl; text-align: right; font-size: 15px;">جناب آقای/سرکار خانم {$safeName}</p>
                            <p dir="rtl" style="margin: 0 0 14px 0; direction: rtl; text-align: right; font-size: 15px;">با سلام و احترام</p>
                            <p dir="rtl" style="margin: 0 0 18px 0; direction: rtl; text-align: right; font-size: 15px; line-height: 2.2;">
                                جهت تحلیل فوری <strong style="color: #0f172a;">{$safeSymbol}</strong> مبلغ 99 هزار تومان به کارت شماره 
                                <span dir="ltr" style="display: inline-block; direction: ltr; unicode-bidi: isolate; font-weight: bold; letter-spacing: 2px; color: #0f172a; background-color: #f1f5f9; padding: 6px 14px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 16px; margin: 4px 0;">6219861913514443</span> 
                                به نام <strong style="color: #0f172a;">رحمان علیمحمدزاده</strong> واریز و رسید آن را در پاسخ به همین ایمیل ارسال فرمایید.
                            </p>
                            <div dir="rtl" style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #f1f5f9; direction: rtl; text-align: right;">
                                <p dir="rtl" style="margin: 0; direction: rtl; text-align: right; font-size: 14px; color: #475569;">با تشکر<br><strong style="color: #0284c7;">tjb24.ir</strong></p>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td dir="rtl" style="background-color: #f8fafc; padding: 14px 26px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #64748b; text-align: center; direction: rtl; font-family: Tahoma, 'Segoe UI', Arial, sans-serif;">
                            وب‌سایت: <a href="https://tjb24.ir" style="color: #0284c7; text-decoration: none; font-weight: bold;" target="_blank">tjb24.ir</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
HTML;
}

// Read and decode input data
$rawBody = file_get_contents('php://input');
$inputData = json_decode($rawBody, true);

if (!is_array($inputData)) {
    $inputData = $_POST;
}

// Extract and sanitize fields
$applicantName   = trim((string)($inputData['applicant_name'] ?? $inputData['name'] ?? ''));
$applicantEmail  = trim((string)($inputData['applicant_email'] ?? $inputData['email'] ?? ''));
$applicantMobile = trim((string)($inputData['applicant_mobile'] ?? $inputData['mobile'] ?? ''));
$userId          = !empty($inputData['user_id']) ? (int)$inputData['user_id'] : null;
$stockSymbol     = trim((string)($inputData['stock_symbol'] ?? $inputData['symbol'] ?? ''));
$requestType     = trim((string)($inputData['request_type'] ?? ''));
$notes          = trim((string)($inputData['notes'] ?? ''));
$clientDeviceInfo = $inputData['device_info'] ?? null;

// Validation
if (mb_strlen($applicantName, 'UTF-8') < 2) {
    http_response_code(422);
    echo json_encode([
        'success' => false,
        'message' => 'لطفاً نام و نام خانوادگی خود را به درستی وارد نمایید.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

if (!filter_var($applicantEmail, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode([
        'success' => false,
        'message' => 'آدرس ایمیل واردشده نامعتبر است.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

if (mb_strlen($stockSymbol, 'UTF-8') < 1) {
    http_response_code(422);
    echo json_encode([
        'success' => false,
        'message' => 'لطفاً نماد یا سهم درخواستی را مشخص فرمایید.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

if (empty($requestType)) {
    http_response_code(422);
    echo json_encode([
        'success' => false,
        'message' => 'انتخاب نوع درخواست الزامی است.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Telemetry & Client Identifiable Details
$clientIp   = getClientIp();
$userAgent  = (string)($_SERVER['HTTP_USER_AGENT'] ?? 'Unknown');
$referer    = (string)($_SERVER['HTTP_REFERER'] ?? '');
$language   = (string)($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '');

$extendedDeviceInfo = [
    'client_telemetry'    => $clientDeviceInfo,
    'server_remote_port'  => $_SERVER['REMOTE_PORT'] ?? null,
    'http_sec_ch_ua'      => $_SERVER['HTTP_SEC_CH_UA'] ?? null,
    'http_sec_ch_ua_platform' => $_SERVER['HTTP_SEC_CH_UA_PLATFORM'] ?? null,
    'http_sec_ch_ua_mobile'   => $_SERVER['HTTP_SEC_CH_UA_MOBILE'] ?? null,
    'request_time'        => date('Y-m-d H:i:s')
];

$deviceInfoJson = json_encode($extendedDeviceInfo, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

// Connect to MariaDB via PDO
try {
    $dsn = sprintf(
        'mysql:host=%s;dbname=%s;charset=%s',
        $dbConfig['host'],
        $dbConfig['dbname'],
        $dbConfig['charset']
    );

    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
    ];

    $pdo = new PDO($dsn, $dbConfig['username'], $dbConfig['password'], $options);

    // Insert record into stock_analysis_requests
    $sql = "INSERT INTO `stock_analysis_requests` (
                `user_id`,
                `applicant_name`,
                `applicant_mobile`,
                `applicant_email`,
                `stock_symbol`,
                `request_type`,
                `notes`,
                `ip_address`,
                `user_agent`,
                `referer`,
                `client_language`,
                `device_info`,
                `status`,
                `created_at`
            ) VALUES (
                :user_id,
                :applicant_name,
                :applicant_mobile,
                :applicant_email,
                :stock_symbol,
                :request_type,
                :notes,
                :ip_address,
                :user_agent,
                :referer,
                :client_language,
                :device_info,
                'pending',
                NOW()
            )";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':user_id'          => $userId,
        ':applicant_name'   => $applicantName,
        ':applicant_mobile' => !empty($applicantMobile) ? $applicantMobile : null,
        ':applicant_email'  => $applicantEmail,
        ':stock_symbol'     => $stockSymbol,
        ':request_type'     => $requestType,
        ':notes'            => !empty($notes) ? $notes : null,
        ':ip_address'       => $clientIp,
        ':user_agent'       => $userAgent,
        ':referer'          => !empty($referer) ? mb_substr($referer, 0, 500, 'UTF-8') : null,
        ':client_language'  => !empty($language) ? mb_substr($language, 0, 100, 'UTF-8') : null,
        ':device_info'      => $deviceInfoJson
    ]);

    $insertId = (int)$pdo->lastInsertId();

    // 1. Send internal notification copy to tahlilreq@tjb24.ir via SMTP (Port 465 SSL)
    try {
        $requestTypeDisplay = ($requestType === '1')
            ? '۱ - تحلیل کامل بنیادی و تکنیکال (رایگان)'
            : (($requestType === '2') ? '۲ - تحلیل کامل بنیادی و تکنیکال و بروزرسانی فوری (۹۹ هزار تومان)' : $requestType);

        $adminSubject = "درخواست تحلیل سهم: {$stockSymbol} (شناسه #{$insertId}) - tjb24.ir";
        $adminHtmlBody = buildAdminNotificationHtml([
            'request_id'           => $insertId,
            'applicant_name'       => $applicantName,
            'applicant_email'      => $applicantEmail,
            'stock_symbol'         => $stockSymbol,
            'request_type'         => $requestTypeDisplay,
            'notes'                => $notes,
            'ip_address'           => $clientIp,
            'user_agent'           => $userAgent,
            'referer'              => $referer,
            'created_at'           => date('Y-m-d H:i:s') . ' UTC',
            'extended_device_info' => $extendedDeviceInfo
        ]);

        sendSmtpMail($smtpConfig, (string)$smtpConfig['to'], $adminSubject, $adminHtmlBody, $applicantEmail);
    } catch (Throwable $mailEx) {
        // Robustness invariant: failure to send email should not affect client response or DB persistence
        error_log('SMTP Notification Email Error in submit_request.php: ' . $mailEx->getMessage());
    }

    // 2. If urgent analysis (requestType == '2'), send payment instruction email to applicant
    $isUrgent = ($requestType === '2' || str_contains($requestType, 'فوری') || str_contains($requestType, '99'));
    if ($isUrgent) {
        try {
            $applicantSubject = "دستورالعمل واریز جهت تحلیل فوری {$stockSymbol} - tjb24.ir";
            $applicantHtmlBody = buildApplicantPaymentInstructionHtml($applicantName, $stockSymbol);
            sendSmtpMail($smtpConfig, $applicantEmail, $applicantSubject, $applicantHtmlBody, (string)$smtpConfig['from']);
        } catch (Throwable $userMailEx) {
            error_log('SMTP Applicant Payment Instruction Error in submit_request.php: ' . $userMailEx->getMessage());
        }
    }

    // Success response: strictly "درخواست شما ثبت شد." per user instruction
    http_response_code(200);
    echo json_encode([
        'success'    => true,
        'message'    => 'درخواست شما ثبت شد.',
        'request_id' => $insertId
    ], JSON_UNESCAPED_UNICODE);

} catch (PDOException $e) {
    error_log('Database Insertion Error in submit_request.php: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'خطا در ارتباط با پایگاه داده. لطفاً دقایقی دیگر مجدداً تلاش فرمایید.'
    ], JSON_UNESCAPED_UNICODE);
} catch (Throwable $t) {
    error_log('Unexpected Exception in submit_request.php: ' . $t->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'خطای سیستمی رخ داد. لطفاً با پشتیبانی تماس بگیرید.'
    ], JSON_UNESCAPED_UNICODE);
}
