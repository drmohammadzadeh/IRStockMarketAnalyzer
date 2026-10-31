<?php
declare(strict_types=1);

/**
 * Gemini Live AI Audio & Text Generation Gateway for Stock Market Reporter
 * Author: alimohammadzadeh@ut.ac.ir
 * Website: tjb24.ir
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if (['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if (['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed. Use POST.'], JSON_UNESCAPED_UNICODE);
    exit;
}

 = file_get_contents('php://input');
 = json_decode((string), true);

if (!is_array()) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON payload.'], JSON_UNESCAPED_UNICODE);
    exit;
}

 = ['prompt'] ?? '';
 = ['systemInstruction'] ?? '';
 = ['apiKey'] ?? '';

if (empty()) {
     = getenv('GEMINI_API_KEY') ?: '';
}

if (empty()) {
    http_response_code(400);
    echo json_encode(['error' => 'Prompt is required.'], JSON_UNESCAPED_UNICODE);
    exit;
}

 = ['gemini-3.8-flash', 'gemini-3.5-flash', 'gemini-2.5-flash'];
 = null;
 = null;

foreach ( as ) {
     = 'https://generativelanguage.googleapis.com/v1beta/models/' .  . ':generateContent?key=' . urlencode();

     = [
        'contents' => [
            [
                'parts' => [
                    ['text' => ]
                ]
            ]
        ],
        'generationConfig' => [
            'temperature' => 0.3,
            'maxOutputTokens' => 2048
        ]
    ];

    if (!empty()) {
        ['systemInstruction'] = [
            'parts' => [
                ['text' => ]
            ]
        ];
    }

     = curl_init();
    curl_setopt(, CURLOPT_URL, );
    curl_setopt(, CURLOPT_POST, true);
    curl_setopt(, CURLOPT_POSTFIELDS, json_encode(, JSON_UNESCAPED_UNICODE));
    curl_setopt(, CURLOPT_RETURNTRANSFER, true);
    curl_setopt(, CURLOPT_HTTPHEADER, ['Content-Type: application/json; charset=utf-8']);
    curl_setopt(, CURLOPT_TIMEOUT, 30);
    curl_setopt(, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt(, CURLOPT_SSL_VERIFYHOST, false);

     = curl_exec();
     = curl_getinfo(, CURLINFO_HTTP_CODE);
     = curl_error();
    curl_close();

    if ( === 200 && !empty()) {
         = json_decode((string), true);
         = ['candidates'] ?? [];
        if (!empty() && isset([0]['content']['parts'][0]['text'])) {
             = [0]['content']['parts'][0]['text'];
            break;
        }
    } else {
         = 'HTTP ' .  . ': ' . ;
    }
}

if ( !== null) {
    echo json_encode([
        'success' => true,
        'text' => trim()
    ], JSON_UNESCAPED_UNICODE);
} else {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to generate analysis from Gemini.',
        'details' => 
    ], JSON_UNESCAPED_UNICODE);
}
