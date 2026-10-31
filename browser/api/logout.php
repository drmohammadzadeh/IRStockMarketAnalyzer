<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

$_SESSION['user'] = null;
unset($_SESSION['user']);
session_destroy();

sendJsonResponse(200, [
    'success' => true,
    'message' => 'با موفقیت از حساب کاربری خارج شدید.'
]);
