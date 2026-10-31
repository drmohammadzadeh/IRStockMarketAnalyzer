<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

$user = getLoggedInUser();

// Accept user_id or mobile or email from session or query param if provided
$input = getJsonInput();
$userId = $user['id'] ?? null;
$mobile = $user['mobile'] ?? trim((string)($_GET['mobile'] ?? ($input['mobile'] ?? '')));
$email  = $user['email'] ?? trim((string)($_GET['email'] ?? ($input['email'] ?? '')));

$pdo = getDbConnection();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // If not logged in and no mobile/email provided
    if (!$userId && empty($mobile) && empty($email)) {
        sendJsonResponse(401, ['success' => false, 'message' => 'برای مشاهده درخواست‌های خود لطفاً ابتدا وارد سامانه شوید.', 'requests' => []]);
    }

    $sql = '
        SELECT id, user_id, applicant_name, applicant_mobile, applicant_email, stock_symbol, 
               request_type, notes, status, analyzed_at, result_url, admin_notes, created_at, updated_at
        FROM stock_analysis_requests
        WHERE 1=0
    ';
    $params = [];

    if ($userId) {
        $sql .= ' OR user_id = :uid';
        $params[':uid'] = $userId;
    }
    if (!empty($mobile)) {
        $sql .= ' OR applicant_mobile = :mob';
        $params[':mob'] = $mobile;
    }
    if (!empty($email)) {
        $sql .= ' OR applicant_email = :em';
        $params[':em'] = $email;
    }

    $sql .= ' ORDER BY id DESC';

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();

    $statusMap = [
        'pending'     => ['text' => 'در صف بررسی', 'badge' => 'badge-pending'],
        'in_progress' => ['text' => 'در حال تحلیل', 'badge' => 'badge-progress'],
        'completed'   => ['text' => 'تحلیل شده', 'badge' => 'badge-completed'],
        'rejected'    => ['text' => 'رد شده', 'badge' => 'badge-rejected']
    ];

    $results = [];
    foreach ($rows as $row) {
        $st = (string)($row['status'] ?? 'pending');
        $meta = $statusMap[$st] ?? ['text' => $st, 'badge' => 'badge-pending'];
        $results[] = [
            'id'             => (int)$row['id'],
            'stock_symbol'   => $row['stock_symbol'],
            'request_type'   => $row['request_type'],
            'notes'          => $row['notes'],
            'status'         => $st,
            'status_label'   => $meta['text'],
            'status_badge'   => $meta['badge'],
            'created_at'     => $row['created_at'],
            'analyzed_at'    => $row['analyzed_at'],
            'result_url'     => $row['result_url'],
            'admin_notes'    => $row['admin_notes']
        ];
    }

    sendJsonResponse(200, [
        'success'  => true,
        'count'    => count($results),
        'requests' => $results
    ]);
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Submit request linked to user
    $applicantName  = trim((string)($input['name'] ?? ($user['first_name'] . ' ' . $user['last_name'] ?? '')));
    $applicantEmail = trim((string)($input['email'] ?? ($user['email'] ?? '')));
    $applicantMobile= trim((string)($input['mobile'] ?? ($user['mobile'] ?? '')));
    $symbol         = trim((string)($input['symbol'] ?? ''));
    $requestType    = trim((string)($input['request_type'] ?? 'تحلیل بنیادی و تکنیکال'));
    $notes          = trim((string)($input['notes'] ?? ''));

    if (empty($symbol)) {
        sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً نام یا نماد سهم درخواستی را مشخص نمایید.']);
    }

    $ip = getClientIp();
    $ua = $_SERVER['HTTP_USER_AGENT'] ?? '';
    $referer = $_SERVER['HTTP_REFERER'] ?? '';
    $lang = $_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '';

    $stmt = $pdo->prepare('
        INSERT INTO stock_analysis_requests 
        (user_id, applicant_name, applicant_mobile, applicant_email, stock_symbol, request_type, notes, ip_address, user_agent, referer, client_language, status)
        VALUES (:uid, :name, :mob, :em, :sym, :rtype, :notes, :ip, :ua, :ref, :lang, "pending")
    ');
    $stmt->execute([
        ':uid'   => $userId,
        ':name'  => $applicantName ?: 'کاربر سامانه',
        ':mob'   => $applicantMobile,
        ':em'    => $applicantEmail ?: ($user['email'] ?? 'no-reply@tjb24.ir'),
        ':sym'   => $symbol,
        ':rtype' => $requestType,
        ':notes' => $notes,
        ':ip'    => $ip,
        ':ua'    => $ua,
        ':ref'   => $referer,
        ':lang'  => $lang
    ]);

    $newId = (int)$pdo->lastInsertId();

    sendJsonResponse(201, [
        'success' => true,
        'message' => 'درخواست تحلیل نماد ' . $symbol . ' با موفقیت ثبت شد.',
        'request_id' => $newId
    ]);
} else {
    sendJsonResponse(405, ['success' => false, 'message' => 'متد ارسالی نامعتبر است.']);
}
