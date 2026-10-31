<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';
require_once __DIR__ . '/mailer.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    sendJsonResponse(405, ['success' => false, 'message' => 'متد ارسالی نامعتبر است.']);
}

$input = getJsonInput();
$identifier = trim((string)($input['identifier'] ?? ($input['mobile'] ?? ($input['email'] ?? ''))));

if (empty($identifier)) {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً شماره موبایل یا آدرس ایمیل خود را وارد نمایید.']);
}

$pdo = getDbConnection();
$stmt = $pdo->prepare('SELECT id, first_name, last_name, mobile, email FROM users WHERE mobile = :i1 OR email = :i2 LIMIT 1');
$stmt->execute([':i1' => $identifier, ':i2' => $identifier]);
$user = $stmt->fetch();

if (!$user) {
    // For security, don't reveal too much, but give helpful feedback
    sendJsonResponse(404, ['success' => false, 'message' => 'حساب کاربری با این مشخصات یافت نشد.']);
}

$userId = (int)$user['id'];
$token = bin2hex(random_bytes(32));
$code = str_pad((string)random_int(100000, 999999), 6, '0', STR_PAD_LEFT);
$expires = date('Y-m-d H:i:s', time() + 3600); // 1 hour

$insert = $pdo->prepare('INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at) VALUES (:uid, :token, :code, :expires)');
$insert->execute([
    ':uid'     => $userId,
    ':token'   => $token,
    ':code'    => $code,
    ':expires' => $expires
]);

$emailSent = sendPasswordResetEmail($user['email'], $user['first_name'] . ' ' . $user['last_name'], $token, $code);

sendJsonResponse(200, [
    'success' => true,
    'message' => 'کد و لینک بازیابی رمز عبور به ایمیل شما ارسال شد.',
    'mobile' => $user['mobile'],
    'email' => $user['email'],
    'email_sent' => $emailSent,
    'debug_token' => $token,
    'debug_code' => $code
]);
