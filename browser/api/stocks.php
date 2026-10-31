<?php
declare(strict_types=1);

/**
 * Server-Side GitHub Watchlist Sync Proxy
 * Website: tjb24.ir
 * Author: alimohammadzadeh@ut.ac.ir
 *
 * Fetches latest stocks.json from GitHub repository, caches it locally
 * on the web server to eliminate CORS issues, client-side filtering blocks,
 * and keep local server files synchronized.
 */

// Headers for JSON and anti-caching
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept, X-Requested-With');
header('Cache-Control: no-cache, no-store, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Expires: 0');

if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$localJsonPath = dirname(__DIR__) . '/data/stocks.json';
$localJsPath   = dirname(__DIR__) . '/data/stocks.js';
$cacheTtl = 60; // 60 seconds auto-refresh

$remotes = [
    'https://raw.githubusercontent.com/drmohammadzadeh/IRStockMarketAnalyzer/main/data/stocks.json',
    'https://fastly.jsdelivr.net/gh/drmohammadzadeh/IRStockMarketAnalyzer@main/data/stocks.json',
    'https://cdn.jsdelivr.net/gh/drmohammadzadeh/IRStockMarketAnalyzer@main/data/stocks.json',
];

$force = isset($_GET['force']) && ($_GET['force'] === '1' || $_GET['force'] === 'true');
$needsRefresh = $force || !file_exists($localJsonPath) || (time() - filemtime($localJsonPath) > $cacheTtl);

$remoteData = null;
$source = 'local-cache';

if ($needsRefresh) {
    foreach ($remotes as $url) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url . '?t=' . time());
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 6);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 3);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_USERAGENT, 'tjb24-stock-sync/1.0');
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);

        $response = curl_exec($ch);
        $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($statusCode === 200 && !empty($response)) {
            $parsed = json_decode((string)$response, true);
            if (is_array($parsed) && count($parsed) > 0) {
                $remoteData = (string)$response;
                $source = $url;
                break;
            }
        }
    }

    if ($remoteData !== null) {
        // Save to local data/stocks.json
        @file_put_contents($localJsonPath, $remoteData, LOCK_EX);

        // Also update local data/stocks.js
        $jsContent = "/**\n * Iranian Stock Market Watchlist Data Store\n * Platform: tjb24.ir\n * Auto-synced from GitHub\n */\nwindow.STOCKS_DATA = " . $remoteData . ";\nif (typeof module !== 'undefined' && module.exports) {\n    module.exports = window.STOCKS_DATA;\n}\n";
        @file_put_contents($localJsPath, $jsContent, LOCK_EX);
    }
}

// Serve content
if ($remoteData !== null) {
    header('X-Data-Source: ' . $source);
    echo $remoteData;
    exit;
}

if (file_exists($localJsonPath)) {
    header('X-Data-Source: local-file');
    echo file_get_contents($localJsonPath);
    exit;
}

http_response_code(500);
echo json_encode([
    'error' => true,
    'message' => 'Failed to load stocks data from GitHub or local storage.'
], JSON_UNESCAPED_UNICODE);