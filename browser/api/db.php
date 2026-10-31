<?php
declare(strict_types=1);

/**
 * Shared Database & Session Configuration for tjb24.ir
 * Database: tjbir_bourse
 * Environment: PHP 8.1+ / MariaDB 10.11+
 */

// Global JSON & CORS Headers
if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');
}

// Handle preflight OPTIONS
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Start PHP Session if not already active
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

/**
 * Get PDO Database Connection
 */
function getDbConnection(): PDO {
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }

    $dbConfig = [
        'host'     => 'localhost',
        'dbname'   => 'tjbir_bourse',
        'username' => 'tjbir_bourse_db_user',
        'password' => '8r0XWGxJI3gOr&?3',
        'charset'  => 'utf8mb4'
    ];

    $dsn = sprintf('mysql:host=%s;dbname=%s;charset=%s', $dbConfig['host'], $dbConfig['dbname'], $dbConfig['charset']);
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
    ];

    try {
        $pdo = new PDO($dsn, $dbConfig['username'], $dbConfig['password'], $options);
        return $pdo;
    } catch (PDOException $e) {
        error_log("Database connection failed: " . $e->getMessage());
        http_response_code(500);
        echo json_encode([
            'success' => false,
            'message' => 'خطای اتصال به پایگاه داده سامانه. لطفاً شکیبا باشید.'
        ], JSON_UNESCAPED_UNICODE);
        exit;
    }
}

/**
 * Send Standard JSON Response
 */
function sendJsonResponse(int $statusCode, array $data): void {
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

/**
 * Extract Client IP Address
 */
function getClientIp(): string {
    $headers = [
        'HTTP_CF_CONNECTING_IP',
        'HTTP_CLIENT_IP',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'
    ];

    foreach ($headers as $header) {
        if (!empty($_SERVER[$header])) {
            $ips = explode(',', (string)$_SERVER[$header]);
            foreach ($ips as $ip) {
                $trimmed = trim($ip);
                if (filter_var($trimmed, FILTER_VALIDATE_IP)) {
                    return $trimmed;
                }
            }
        }
    }

    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

/**
 * Read and Decode Request JSON Body
 */
function getJsonInput(): array {
    $raw = file_get_contents('php://input');
    if (empty($raw)) {
        return $_POST;
    }
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : [];
}

/**
 * Get Currently Logged-in User from Session
 */
function getLoggedInUser(): ?array {
    if (!empty($_SESSION['user']) && is_array($_SESSION['user'])) {
        return $_SESSION['user'];
    }
    return null;
}
