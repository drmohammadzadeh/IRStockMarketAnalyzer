<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';

$user = getLoggedInUser();

if ($user) {
    sendJsonResponse(200, [
        'logged_in' => true,
        'user'      => $user
    ]);
} else {
    sendJsonResponse(200, [
        'logged_in' => false,
        'user'      => null
    ]);
}
