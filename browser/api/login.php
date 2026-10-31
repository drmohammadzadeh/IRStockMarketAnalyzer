<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    sendJsonResponse(405, ['success' => false, 'message' => 'متد ارسالی نامعتبر است.']);
}

$input = getJsonInput();
$username = trim((string)($input['username'] ?? ($input['mobile'] ?? '')));
$password = (string)($input['password'] ?? '');

if (empty($username) || empty($password)) {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً نام کاربری (شماره موبایل) و رمز عبور را وارد فرمایید.']);
}

$pdo = getDbConnection();

$stmt = $pdo->prepare('SELECT id, first_name, last_name, mobile, email, password_hash, is_active FROM users WHERE mobile = :u1 OR email = :u2 LIMIT 1');
$stmt->execute([':u1' => $username, ':u2' => $username]);
$user = $stmt->fetch();

if (!$user || !password_verify($password, (string)$user['password_hash'])) {
    sendJsonResponse(401, ['success' => false, 'message' => 'شماره موبایل یا رمز عبور اشتباه است.']);
}

if ((int)$user['is_active'] === 0) {
    sendJsonResponse(403, [
        'success' => false,
        'need_activation' => true,
        'mobile' => $user['mobile'],
        'email' => $user['email'],
        'message' => 'حساب کاربری شما هنوز فعال نشده است. لطفاً کد فعال‌سازی ارسال‌شده به ایمیلتان را وارد کنید.'
    ]);
}

// Update last login
$update = $pdo->prepare('UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = :id');
$update->execute([':id' => $user['id']]);

$userData = [
    'id'         => (int)$user['id'],
    'first_name' => $user['first_name'],
    'last_name'  => $user['last_name'],
    'mobile'     => $user['mobile'],
    'email'      => $user['email']
];

$_SESSION['user'] = $userData;

sendJsonResponse(200, [
    'success' => true,
    'message' => 'با موفقیت وارد شدید. خوش آمدید!',
    'user'    => $userData
]);
