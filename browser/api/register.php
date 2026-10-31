<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';
require_once __DIR__ . '/mailer.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    sendJsonResponse(405, ['success' => false, 'message' => 'متد ارسالی نامعتبر است.']);
}

$input = getJsonInput();

$firstName = trim((string)($input['first_name'] ?? ''));
$lastName  = trim((string)($input['last_name'] ?? ''));
$mobile    = trim((string)($input['mobile'] ?? ''));
$email     = trim((string)($input['email'] ?? ''));
$password  = (string)($input['password'] ?? '');

// Validation
if (empty($firstName) || empty($lastName)) {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً نام و نام خانوادگی خود را کامل وارد نمایید.']);
}

// Mobile check: 09xxxxxxxxx (11 digits)
if (!preg_match('/^09\d{9}$/', $mobile)) {
    sendJsonResponse(400, ['success' => false, 'message' => 'شماره موبایل نامعتبر است. شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد.']);
}

// Email check
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً یک آدرس ایمیل معتبر وارد نمایید.']);
}

// Password check
if (mb_strlen($password) < 6) {
    sendJsonResponse(400, ['success' => false, 'message' => 'رمز عبور باید حداقل ۶ کاراکتر باشد.']);
}

$pdo = getDbConnection();

// Check duplicate mobile or email
$stmt = $pdo->prepare('SELECT id, is_active FROM users WHERE mobile = :mobile OR email = :email LIMIT 1');
$stmt->execute([':mobile' => $mobile, ':email' => $email]);
$existing = $stmt->fetch();

if ($existing) {
    if ((int)$existing['is_active'] === 0) {
        // Account exists but inactive; generate fresh activation code
        $userId = (int)$existing['id'];
        $token = bin2hex(random_bytes(32));
        $code = str_pad((string)random_int(100000, 999999), 6, '0', STR_PAD_LEFT);
        $expires = date('Y-m-d H:i:s', time() + 86400);

        $actStmt = $pdo->prepare('INSERT INTO user_activations (user_id, activation_token, activation_code, expires_at) VALUES (:uid, :token, :code, :expires)');
        $actStmt->execute([':uid' => $userId, ':token' => $token, ':code' => $code, ':expires' => $expires]);

        sendActivationEmail($email, $firstName . ' ' . $lastName, $mobile, $token, $code);

        sendJsonResponse(200, [
            'success' => true,
            'need_activation' => true,
            'mobile' => $mobile,
            'email' => $email,
            'message' => 'حساب شما قبلاً ثبت شده اما هنوز فعال نشده است. کد فعال‌سازی جدید به ایمیل شما ارسال گردید.',
            'debug_token' => $token,
            'debug_code' => $code
        ]);
    } else {
        sendJsonResponse(400, ['success' => false, 'message' => 'کاربری با این شماره موبایل یا ایمیل قبلاً ثبت‌نام کرده و فعال است. لطفاً وارد شوید.']);
    }
}

// Create new user
$passwordHash = password_hash($password, PASSWORD_BCRYPT);
$insertUser = $pdo->prepare('INSERT INTO users (first_name, last_name, mobile, email, password_hash, is_active) VALUES (:fn, :ln, :mob, :em, :hash, 0)');
$insertUser->execute([
    ':fn'   => $firstName,
    ':ln'   => $lastName,
    ':mob'  => $mobile,
    ':em'   => $email,
    ':hash' => $passwordHash
]);

$userId = (int)$pdo->lastInsertId();

// Generate activation token & 6-digit code
$token = bin2hex(random_bytes(32));
$code = str_pad((string)random_int(100000, 999999), 6, '0', STR_PAD_LEFT);
$expires = date('Y-m-d H:i:s', time() + 86400); // 24 hours

$actStmt = $pdo->prepare('INSERT INTO user_activations (user_id, activation_token, activation_code, expires_at) VALUES (:uid, :token, :code, :expires)');
$actStmt->execute([
    ':uid'     => $userId,
    ':token'   => $token,
    ':code'    => $code,
    ':expires' => $expires
]);

// Dispatch email
$emailSent = sendActivationEmail($email, $firstName . ' ' . $lastName, $mobile, $token, $code);

sendJsonResponse(201, [
    'success' => true,
    'message' => 'ثبت‌نام شما با موفقیت انجام شد. لینک و کد فعال‌سازی ۶ رقمی به ایمیل شما ارسال گردید.',
    'mobile' => $mobile,
    'email' => $email,
    'email_sent' => $emailSent,
    'debug_token' => $token,
    'debug_code' => $code
]);
