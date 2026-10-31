<?php
declare(strict_types=1);

/**
 * Live Stock Reporter Voice Chat API
 * Website: tjb24.ir
 * Author: alimohammadzadeh@ut.ac.ir
 * 
 * Answers user's voice question via Gemini and synthesizes audio WAV speech.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');

if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Method not allowed. Use POST.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$rawInput = file_get_contents('php://input');
$payload = json_decode((string)$rawInput, true);

if (!is_array($payload)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid JSON input.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$symbol = trim((string)($payload['symbol'] ?? ''));
$question = trim((string)($payload['question'] ?? ''));
$marketContext = trim((string)($payload['market_context'] ?? ''));

if (empty($question)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Question is required.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$apiKey = trim((string)($payload['apiKey'] ?? ''));
if (empty($apiKey)) {
    $apiKey = getenv('GEMINI_API_KEY') ?: '';
}

function httpPostJson(string $url, array $data, int $timeout = 8): ?string {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data, JSON_UNESCAPED_UNICODE));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json; charset=utf-8',
        'Accept: application/json'
    ]);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ($code === 200 && !empty($resp)) ? (string)$resp : null;
}

function pcmToWav(string $pcmBytes, int $sampleRate = 24000, int $channels = 1, int $bitsPerSample = 16): string {
    $byteRate = (int)($sampleRate * $channels * ($bitsPerSample / 8));
    $blockAlign = (int)($channels * ($bitsPerSample / 8));
    $dataSize = strlen($pcmBytes);
    $chunkSize = 36 + $dataSize;

    $header = pack('a4Va4a4VvvVVvva4V',
        'RIFF',
        $chunkSize,
        'WAVE',
        'fmt ',
        16, // Subchunk1Size
        1,  // AudioFormat (PCM)
        $channels,
        $sampleRate,
        $byteRate,
        $blockAlign,
        $bitsPerSample,
        'data',
        $dataSize
    );
    return $header . $pcmBytes;
}

// 1. Generate Answer via Gemini
$prompt = "کاربر درباره نماد {$symbol} این سوال را مطرح کرده است:\n«{$question}»\n\n" .
    "اطلاعات تابلوی نماد:\n{$marketContext}\n\n" .
    "به عنوان تحلیل‌گر ارشد بورس، در ۲ الی ۳ جمله رسا، روشن و فارسی به صورت مستقیم و بدون مقدمه‌چینی به سوال پاسخ بده. بدون ستاره و مارک‌داون.";

$systemInstruction = "تو تحلیل‌گر ارشد بازار سرمایه هستی. پاسخ کوتاه، دقیق، فارسی و حرفه‌ای بده.";

$candidateModels = ['gemini-flash-lite-latest', 'gemini-2.5-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite'];
$answerText = null;

foreach ($candidateModels as $model) {
    $url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key=" . urlencode($apiKey);
    $resp = httpPostJson($url, [
        'contents' => [['parts' => [['text' => $prompt]]]],
        'systemInstruction' => ['parts' => [['text' => $systemInstruction]]],
        'generationConfig' => ['temperature' => 0.3, 'maxOutputTokens' => 600]
    ], 8);

    if ($resp) {
        $json = json_decode($resp, true);
        if (!empty($json['candidates'][0]['content']['parts'][0]['text'])) {
            $answerText = trim($json['candidates'][0]['content']['parts'][0]['text']);
            break;
        }
    }
}

if (!$answerText) {
    $answerText = "با توجه به وضعیت فعلی تابلوی نماد {$symbol} و حجم معاملات، توصیه می‌شود نسبت قدرت خریدار و جریان نقدینگی را در دقایق آتی زیر نظر داشته باشید.";
}

// 2. Synthesize Speech Audio (WAV) via Gemini TTS with Male Voice (Charon) if quota allows
$candidateTts = ['gemini-2.5-flash-preview-tts'];
$audioBase64 = null;
$cleanTtsText = str_replace(['*', '#', '_'], '', $answerText);

foreach ($candidateTts as $ttsModel) {
    $ttsUrl = "https://generativelanguage.googleapis.com/v1beta/models/{$ttsModel}:generateContent?key=" . urlencode($apiKey);
    $ttsPayload = [
        'contents' => [['parts' => [['text' => $cleanTtsText]]]],
        'generationConfig' => [
            'responseModalities' => ['AUDIO'],
            'speechConfig' => [
                'voiceConfig' => [
                    'prebuiltVoiceConfig' => [
                        'voiceName' => 'Charon'
                    ]
                ]
            ]
        ]
    ];
    $resp = httpPostJson($ttsUrl, $ttsPayload, 3);

    if ($resp) {
        $json = json_decode($resp, true);
        $parts = $json['candidates'][0]['content']['parts'] ?? [];
        foreach ($parts as $p) {
            if (!empty($p['inlineData']['data'])) {
                $rawPcm = base64_decode($p['inlineData']['data']);
                if (substr($rawPcm, 0, 4) !== 'RIFF') {
                    $wavBytes = pcmToWav($rawPcm, 24000, 1, 16);
                    $audioBase64 = base64_encode($wavBytes);
                } else {
                    $audioBase64 = $p['inlineData']['data'];
                }
                break 2;
            }
        }
    }
}

echo json_encode([
    'success' => true,
    'answer_text' => $answerText,
    'audio_base64' => $audioBase64 ?: ''
], JSON_UNESCAPED_UNICODE);
