<?php
declare(strict_types=1);

/**
 * Pure PHP SMTP Email Sender over SSL (Port 465)
 * Website: tjb24.ir
 */

function getSmtpConfig(): array {
    return [
        'host'     => 'mail.tjb24.ir',
        'port'     => 465,
        'username' => 'tahlilreq@tjb24.ir',
        'password' => 'Tjb24$$1234',
        'from'     => 'tahlilreq@tjb24.ir',
        'from_name'=> 'سامانه تحلیل بازار سرمایه (tjb24.ir)',
        'timeout'  => 10
    ];
}

function sendSmtpMail(string $to, string $subject, string $htmlBody, ?string $replyTo = null): bool {
    $config   = getSmtpConfig();
    $host     = (string)$config['host'];
    $port     = (int)$config['port'];
    $timeout  = (int)($config['timeout'] ?? 10);
    $username = (string)$config['username'];
    $password = (string)$config['password'];
    $from     = (string)$config['from'];
    $fromName = (string)($config['from_name'] ?? 'tjb24.ir');

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
        error_log("SMTP connection failed: {$errstr} ({$errno})");
        return false;
    }

    stream_set_timeout($socket, $timeout);

    $readResponse = function() use ($socket): string {
        $response = '';
        while (!feof($socket)) {
            $line = fgets($socket, 2048);
            if ($line === false) break;
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
            throw new RuntimeException("SMTP Command [{$cmd}] failed: {$res}");
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
        $encodedFromName = '=?UTF-8?B?' . base64_encode($fromName) . '?=';
        $messageId = sprintf('<%s.%s@tjb24.ir>', uniqid((string)time(), true), bin2hex(random_bytes(4)));

        $headers = [
            'From: ' . $encodedFromName . ' <' . $from . '>',
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
        $sendCommand('QUIT', [221]);
        @fclose($socket);
        return true;
    } catch (\Throwable $e) {
        error_log("Error sending SMTP mail: " . $e->getMessage());
        @fclose($socket);
        return false;
    }
}

/**
 * Send Account Activation Email
 */
function sendActivationEmail(string $toEmail, string $name, string $mobile, string $token, string $code): bool {
    $activationUrl = "https://tjb24.ir/?action=activate&token=" . urlencode($token);
    $subject = "فعال‌سازی حساب کاربری در سامانه تحلیل بازار سرمایه (tjb24.ir)";

    $html = <<<HTML
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
body { font-family: Tahoma, 'Vazirmatn', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #1e293b; direction: rtl; }
.card { max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.06); }
.header { background: linear-gradient(135deg, #1e3a8a, #0284c7); padding: 28px 24px; text-align: center; color: #ffffff; }
.header h1 { margin: 0; font-size: 20px; font-weight: bold; }
.body { padding: 28px 24px; font-size: 14px; line-height: 1.8; }
.code-box { background: #f1f5f9; border: 2px dashed #0284c7; border-radius: 10px; padding: 16px; text-align: center; margin: 20px 0; }
.code-digits { font-size: 28px; font-weight: 800; letter-spacing: 6px; color: #1e3a8a; font-family: monospace, Arial; }
.btn-activate { display: inline-block; background: #0284c7; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; margin: 15px 0; }
.footer { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; font-size: 12px; color: #64748b; text-align: center; }
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <h1>سامانه تحلیل هوشمند بازار سرمایه ایران (tjb24.ir)</h1>
    </div>
    <div class="body">
        <p>کاربر گرامی <strong>{$name}</strong> عزیز، با سلام و درود؛</p>
        <p>از اینکه به جمع تحلیل‌گران و سرمایه‌گذاران سامانه <strong>tjb24.ir</strong> پیوستید خرسندیم. نام کاربری شما شماره موبایل <strong>{$mobile}</strong> می‌باشد.</p>
        <p>برای فعال‌سازی اکانت و بهره‌مندی از تمامی امکانات و تحلیل‌های ۱۷ نماد بازار سرمایه، می‌توانید به یکی از دو روش زیر اقدام فرمایید:</p>
        
        <p><strong>روش اول:</strong> ورود کد فعال‌سازی ۶ رقمی زیر در صفحه سایت:</p>
        <div class="code-box">
            <div class="code-digits">{$code}</div>
        </div>

        <p><strong>روش دوم:</strong> کلیک مستقیم بر روی دکمه فعال‌سازی فوری:</p>
        <div style="text-align: center;">
            <a href="{$activationUrl}" class="btn-activate">فعال‌سازی و ورود به حساب کاربری</a>
        </div>
        <p style="font-size: 12px; color: #94a3b8; word-break: break-all;">یا آدرس زیر را در مرورگر خود کپی کنید:<br>{$activationUrl}</p>
        
        <p>این کد و لینک به مدت ۲۴ ساعت معتبر می‌باشد.</p>
    </div>
    <div class="footer">
        © ۲۰۲۶ تمامی حقوق محفوظ است | سامانه تحلیل بازار سرمایه ایران (tjb24.ir)
    </div>
</div>
</body>
</html>
HTML;

    return sendSmtpMail($toEmail, $subject, $html);
}

/**
 * Send Password Reset Email
 */
function sendPasswordResetEmail(string $toEmail, string $name, string $token, string $code): bool {
    $resetUrl = "https://tjb24.ir/?action=reset_password&token=" . urlencode($token);
    $subject = "درخواست بازیابی رمز عبور در سامانه tjb24.ir";

    $html = <<<HTML
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
body { font-family: Tahoma, 'Vazirmatn', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #1e293b; direction: rtl; }
.card { max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.06); }
.header { background: linear-gradient(135deg, #1e3a8a, #dc2626); padding: 28px 24px; text-align: center; color: #ffffff; }
.header h1 { margin: 0; font-size: 20px; font-weight: bold; }
.body { padding: 28px 24px; font-size: 14px; line-height: 1.8; }
.code-box { background: #fef2f2; border: 2px dashed #dc2626; border-radius: 10px; padding: 16px; text-align: center; margin: 20px 0; }
.code-digits { font-size: 28px; font-weight: 800; letter-spacing: 6px; color: #991b1b; font-family: monospace, Arial; }
.btn-reset { display: inline-block; background: #dc2626; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; margin: 15px 0; }
.footer { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; font-size: 12px; color: #64748b; text-align: center; }
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <h1>بازیابی رمز عبور در سامانه tjb24.ir</h1>
    </div>
    <div class="body">
        <p>کاربر گرامی <strong>{$name}</strong> عزیز،</p>
        <p>درخواستی مبنی بر بازیابی رمز عبور برای حساب کاربری شما دریافت شده است. در صورتی که این درخواست توسط خودتان ثبت شده، می‌توانید از طریق یکی از گزینه‌های زیر اقدام نمایید:</p>

        <p><strong>روش اول:</strong> ورود کد تایید ۶ رقمی در فرم تغییر رمز عبور:</p>
        <div class="code-box">
            <div class="code-digits">{$code}</div>
        </div>

        <p><strong>روش دوم:</strong> کلیک مستقیم بر روی دکمه زیر جهت بازنشانی رمز:</p>
        <div style="text-align: center;">
            <a href="{$resetUrl}" class="btn-reset">بازنشانی رمز عبور</a>
        </div>
        <p style="font-size: 12px; color: #94a3b8; word-break: break-all;">یا لینک زیر را باز کنید:<br>{$resetUrl}</p>

        <p>این کد و لینک به مدت ۱ ساعت معتبر است. در صورتی که شما این درخواست را نداده‌اید، می‌توانید این پیام را نادیده بگیرید.</p>
    </div>
    <div class="footer">
        © ۲۰۲۶ تمامی حقوق محفوظ است | سامانه تحلیل بازار سرمایه ایران (tjb24.ir)
    </div>
</div>
</body>
</html>
HTML;

    return sendSmtpMail($toEmail, $subject, $html);
}
