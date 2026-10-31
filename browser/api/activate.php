<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

$input = getJsonInput();

$token  = trim((string)($input['token'] ?? ($_GET['token'] ?? '')));
$mobile = trim((string)($input['mobile'] ?? ''));
$code   = trim((string)($input['code'] ?? ''));

$pdo = getDbConnection();
$activationRecord = null;
$userId = null;

if (!empty($token)) {
    // Activate via unique token
    $stmt = $pdo->prepare('
        SELECT ua.id, ua.user_id, ua.is_used, ua.expires_at, u.first_name, u.last_name, u.mobile, u.email
        FROM user_activations ua
        JOIN users u ON u.id = ua.user_id
        WHERE ua.activation_token = :token
        LIMIT 1
    ');
    $stmt->execute([':token' => $token]);
    $activationRecord = $stmt->fetch();
} elseif (!empty($mobile) && !empty($code)) {
    // Activate via mobile and 6-digit code
    $stmt = $pdo->prepare('
        SELECT ua.id, ua.user_id, ua.is_used, ua.expires_at, u.first_name, u.last_name, u.mobile, u.email
        FROM user_activations ua
        JOIN users u ON u.id = ua.user_id
        WHERE u.mobile = :mobile AND ua.activation_code = :code
        ORDER BY ua.id DESC
        LIMIT 1
    ');
    $stmt->execute([':mobile' => $mobile, ':code' => $code]);
    $activationRecord = $stmt->fetch();
} else {
    sendJsonResponse(400, ['success' => false, 'message' => 'لطفاً توکن فعال‌سازی یا شماره موبایل و کد ۶ رقمی را وارد نمایید.']);
}

if (!$activationRecord) {
    sendJsonResponse(404, ['success' => false, 'message' => 'کد یا لینک فعال‌سازی یافت نشد یا معتبر نمی‌باشد.']);
}

if ((int)$activationRecord['is_used'] === 1) {
    sendJsonResponse(400, ['success' => false, 'message' => 'این کد یا لینک فعال‌سازی قبلاً استفاده شده است. لطفاً وارد شوید.']);
}

if (strtotime($activationRecord['expires_at']) < time()) {
    sendJsonResponse(400, ['success' => false, 'message' => 'مهلت استفاده از این کد یا لینک به پایان رسیده است. لطفاً مجدداً درخواست ارسال کد نمایید.']);
}

$userId = (int)$activationRecord['user_id'];

// Mark activation as used
$updateAct = $pdo->prepare('UPDATE user_activations SET is_used = 1 WHERE id = :id');
$updateAct->execute([':id' => $activationRecord['id']]);

// Activate user
$updateUser = $pdo->prepare('UPDATE users SET is_active = 1, last_login_at = CURRENT_TIMESTAMP WHERE id = :uid');
$updateUser->execute([':uid' => $userId]);

$userData = [
    'id'         => $userId,
    'first_name' => $activationRecord['first_name'],
    'last_name'  => $activationRecord['last_name'],
    'mobile'     => $activationRecord['mobile'],
    'email'      => $activationRecord['email']
];

$_SESSION['user'] = $userData;

sendJsonResponse(200, [
    'success' => true,
    'message' => 'حساب کاربری شما با موفقیت فعال شد و هم‌اکنون وارد سامانه شدید.',
    'user'    => $userData
]);
