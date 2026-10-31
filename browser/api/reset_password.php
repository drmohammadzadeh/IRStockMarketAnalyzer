<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    sendJsonResponse(405, ['success' => false, 'message' => 'متد ارسالی نامعتبر است.']);
}

$input = getJsonInput();
$token       = trim((string)($input['token'] ?? ''));
$mobile      = trim((string)($input['mobile'] ?? ''));
$code        = trim((string)($input['code'] ?? ''));
$newPassword = (string)($input['new_password'] ?? ($input['password'] ?? ''));

if (mb_strlen($newPassword) < 6) {
    sendJsonResponse(400, ['success' => false, 'message' => 'رمز عبور جدید باید حداقل ۶ کاراکتر باشد.']);
}

$pdo = getDbConnection();
$resetRecord = null;

if (!empty($token)) {
    $stmt = $pdo->prepare('
        SELECT pr.id, pr.user_id, pr.is_used, pr.expires_at, u.mobile, u.email
        FROM password_resets pr
        JOIN users u ON u.id = pr.user_id
        WHERE pr.reset_token = :token
        LIMIT 1
    ');
    $stmt->execute([':token' => $token]);
    $resetRecord = $stmt->fetch();
} elseif (!empty($mobile) && !empty($code)) {
    $stmt = $pdo->prepare('
        SELECT pr.id, pr.user_id, pr.is_used, pr.expires_at, u.mobile, u.email
        FROM password_resets pr
        JOIN users u ON u.id = pr.user_id
        WHERE u.mobile = :mobile AND pr.reset_code = :code
        ORDER BY pr.id DESC
        LIMIT 1
    ');
    $stmt->execute([':mobile' => $mobile, ':code' => $code]);
    $resetRecord = $stmt->fetch();
} else {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً توکن بازیابی یا شماره موبایل و کد ۶ رقمی را وارد نمایید.']);
}

if (!$resetRecord) {
    sendJsonResponse(404, ['success' => false, 'message' => 'کد یا لینک بازیابی رمز یافت نشد یا معتبر نیست.']);
}

if ((int)$resetRecord['is_used'] === 1) {
    sendJsonResponse(400, ['success' => false, 'message' => 'این کد بازیابی قبلاً استفاده شده است.']);
}

if (strtotime($resetRecord['expires_at']) < time()) {
    sendJsonResponse(400, ['success' => false, 'message' => 'مهلت استفاده از این کد به پایان رسیده است. لطفاً مجدداً درخواست نمایید.']);
}

$userId = (int)$resetRecord['user_id'];
$hash = password_hash($newPassword, PASSWORD_BCRYPT);

// Update user password and ensure active
$upUser = $pdo->prepare('UPDATE users SET password_hash = :hash, is_active = 1 WHERE id = :uid');
$upUser->execute([':hash' => $hash, ':uid' => $userId]);

// Mark reset used
$upReset = $pdo->prepare('UPDATE password_resets SET is_used = 1 WHERE id = :id');
$upReset->execute([':id' => $resetRecord['id']]);

sendJsonResponse(200, [
    'success' => true,
    'message' => 'رمز عبور شما با موفقیت تغییر یافت. اکنون می‌توانید با رمز عبور جدید وارد شوید.'
]);
