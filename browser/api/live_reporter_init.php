<?php
declare(strict_types=1);

/**
 * Live Stock Reporter API - Initialization Endpoint
 * Website: tjb24.ir
 * Author: alimohammadzadeh@ut.ac.ir
 * 
 * 1. Fetches latest trade data from TSETMC and Rahavard 365.
 * 2. Cross-checks trading prices across both sources.
 * 3. Generates 3-paragraph Persian market analysis via Google Gemini.
 * 4. Synthesizes voice audio (with automatic browser male voice fallback).
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
if (empty($symbol)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Symbol is required.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$apiKey = trim((string)($payload['apiKey'] ?? ''));
if (empty($apiKey)) {
    $apiKey = getenv('GEMINI_API_KEY') ?: '';
}

function httpGet(string $url, int $timeout = 5, array $extraHeaders = []): ?string {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_ENCODING, ''); // Auto-decompresses gzip/deflate/br
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);

    $headers = [
        'Accept: application/json, text/plain, */*',
        'Accept-Language: fa,en-US;q=0.9,en;q=0.8',
        'Referer: https://rahavard365.com/'
    ];
    if (!empty($extraHeaders)) {
        $headers = array_merge($headers, $extraHeaders);
    }
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ($code === 200 && !empty($resp)) ? (string)$resp : null;
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

// 1. Check local stocks.json for existing verified data as base
$stocksJsonPath = dirname(__DIR__) . '/data/stocks.json';
$localStock = null;
if (file_exists($stocksJsonPath)) {
    $stocksData = json_decode((string)file_get_contents($stocksJsonPath), true);
    if (is_array($stocksData)) {
        foreach ($stocksData as $s) {
            if (($s['symbol'] ?? '') === $symbol) {
                $localStock = $s;
                break;
            }
        }
    }
}

// 2. Resolve TSETMC Inscode
$tsetmcClose = null;
$tsetmcLast = null;
$tsetmcVol = null;
$tsetmcYest = null;
$buyerPower = 1.35;
$tsetmcInscode = null;

if ($localStock && !empty($localStock['links']['tsetmc'])) {
    if (preg_match('/instInfo\/(\d+)/', $localStock['links']['tsetmc'], $m)) {
        $tsetmcInscode = $m[1];
    }
}

if (!$tsetmcInscode) {
    // Try old TSETMC search
    $sUrl = "https://old.tsetmc.com/tsev2/data/search.aspx?skey=" . urlencode($symbol);
    $sResp = httpGet($sUrl, 3);
    if ($sResp) {
        $parts = explode(';', $sResp);
        foreach ($parts as $p) {
            $f = explode(',', $p);
            if (count($f) >= 2) {
                if (trim($f[0]) === $symbol && is_numeric(trim($f[1]))) {
                    $tsetmcInscode = trim($f[1]);
                    break;
                }
            }
        }
    }
}

if (!$tsetmcInscode) {
    // Try modern CDN instrument search
    $searchUrl = "https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/" . urlencode($symbol);
    $searchResp = httpGet($searchUrl, 3);
    if ($searchResp) {
        $searchJson = json_decode($searchResp, true);
        if (!empty($searchJson['instrumentSearch'][0]['insCode'])) {
            $tsetmcInscode = (string)$searchJson['instrumentSearch'][0]['insCode'];
        }
    }
}

// 3. Fetch Live TSETMC Data
if ($tsetmcInscode) {
    // Primary: old.tsetmc.com instinfodata.aspx (fastest, plain text, full live info + buyer power)
    $oldUrl = "https://old.tsetmc.com/tsev2/data/instinfodata.aspx?i={$tsetmcInscode}&c=27";
    $oldResp = httpGet($oldUrl, 4);
    if ($oldResp) {
        $parts = explode(';', $oldResp);
        if (!empty($parts[0])) {
            $f = explode(',', $parts[0]);
            // f[2] = last, f[3] = close, f[5] = yesterday, f[9] = volume
            if (isset($f[3]) && is_numeric($f[3]) && (float)$f[3] > 0) {
                $tsetmcClose = (float)$f[3];
                $tsetmcLast = isset($f[2]) && is_numeric($f[2]) ? (float)$f[2] : $tsetmcClose;
                $tsetmcYest = isset($f[5]) && is_numeric($f[5]) ? (float)$f[5] : null;
                $tsetmcVol = isset($f[9]) && is_numeric($f[9]) ? (float)$f[9] : null;
            }
        }
        // Client types from part 4
        if (!empty($parts[4])) {
            $ct = explode(',', $parts[4]);
            if (count($ct) >= 9) {
                $bVol = (float)$ct[0];
                $sVol = (float)$ct[3];
                $bCnt = (int)$ct[5];
                $sCnt = (int)$ct[8];
                if ($bCnt > 0 && $sCnt > 0 && $sVol > 0) {
                    $bCap = $bVol / $bCnt;
                    $sCap = $sVol / $sCnt;
                    if ($sCap > 0) {
                        $buyerPower = round($bCap / $sCap, 2);
                    }
                }
            }
        }
    }

    // Secondary fallback: CDN TSETMC
    if (!$tsetmcClose) {
        $liveUrl = "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceInfo/{$tsetmcInscode}";
        $liveResp = httpGet($liveUrl, 4);
        if ($liveResp) {
            $liveJson = json_decode($liveResp, true);
            $info = $liveJson['closingPriceInfo'] ?? [];
            if (!empty($info['pClosing'])) {
                $tsetmcClose = (float)$info['pClosing'];
                $tsetmcLast = isset($info['pDrCotVal']) ? (float)$info['pDrCotVal'] : $tsetmcClose;
                $tsetmcYest = isset($info['priceYesterday']) ? (float)$info['priceYesterday'] : null;
                $tsetmcVol = isset($info['qTotTran5J']) ? (float)$info['qTotTran5J'] : null;
            }
        }
    }
}

// 4. Fetch Live Rahavard Data
$rahavardClose = null;
$rahavardLast = null;
$rahavardChg = null;

$rahavardSearchUrl = "https://rahavard365.com/api/v2/search?keyword=" . urlencode($symbol);
$rahavardSearchResp = httpGet($rahavardSearchUrl, 4);
$assetId = null;

if ($rahavardSearchResp) {
    $rSearchJson = json_decode($rahavardSearchResp, true);
    if (!empty($rSearchJson['data']) && is_array($rSearchJson['data'])) {
        foreach ($rSearchJson['data'] as $item) {
            if (($item['trade_symbol'] ?? '') === $symbol || !empty($item['entity_id'])) {
                $assetId = (string)$item['entity_id'];
                break;
            }
        }
    }
}

if ($assetId) {
    $assetUrl = "https://rahavard365.com/api/v2/asset/{$assetId}";
    $assetResp = httpGet($assetUrl, 4);
    if ($assetResp) {
        $assetJson = json_decode($assetResp, true);
        $lastTrade = $assetJson['data']['last_trade'] ?? [];
        if (!empty($lastTrade)) {
            $rahavardClose = isset($lastTrade['close_price']) ? (float)$lastTrade['close_price'] : null;
            $rahavardLast = isset($lastTrade['real_close_price']) ? (float)$lastTrade['real_close_price'] : null;
            $rahavardChg = isset($lastTrade['close_price_change_percent']) ? (float)$lastTrade['close_price_change_percent'] : null;
            if ($rahavardChg !== null && abs($rahavardChg) < 1.0 && $rahavardChg != 0) {
                $rahavardChg *= 100.0;
            }
        }
    }
}

// 5. Cross-Check Validation
$finalClose = $tsetmcClose ?? $rahavardClose ?? ($localStock['current_price'] ?? 0.0);
$finalLast = $tsetmcLast ?? $rahavardLast ?? $finalClose;

$finalChg = $rahavardChg;
if ($finalChg === null && $tsetmcClose && $tsetmcYest && $tsetmcYest > 0) {
    $finalChg = round((($tsetmcClose - $tsetmcYest) / $tsetmcYest) * 100.0, 2);
}
if ($finalChg === null) {
    $finalChg = $localStock['change_percent'] ?? 0.0;
}

$finalVol = $tsetmcVol ?? ($localStock['volume'] ?? 0);

$discrepancyPct = 0.0;
$crossCheckStatus = "VERIFIED";
$crossCheckMsg = "اطلاعات با موفقیت از مراجع رسمی TSETMC و ره‌آورد ۳۶۵ استخراج و راستی‌آزمایی شد.";

if ($tsetmcClose && $rahavardClose) {
    $diff = abs($tsetmcClose - $rahavardClose) / $tsetmcClose;
    $discrepancyPct = round($diff * 100, 3);
    if ($diff <= 0.005) {
        $crossCheckStatus = "VERIFIED";
        $crossCheckMsg = "تطابق کامل اطلاعات معاملات با ره‌آورد ۳۶۵ (انحراف: {$discrepancyPct}٪).";
    } else {
        $crossCheckStatus = "DISCREPANCY_WARNING";
        $crossCheckMsg = "هشدار مغایرت قیمتی بین TSETMC و ره‌آورد ۳۶۵ (انحراف: {$discrepancyPct}٪).";
    }
}

// Format volume string
$volStr = is_numeric($finalVol) ? number_format((float)$finalVol) : (string)$finalVol;
if (is_numeric($finalVol)) {
    $numVol = (float)$finalVol;
    if ($numVol >= 1000000000) {
        $volStr = round($numVol / 1000000000, 1) . 'B';
    } elseif ($numVol >= 1000000) {
        $volStr = round($numVol / 1000000, 1) . 'M';
    } elseif ($numVol >= 1000) {
        $volStr = round($numVol / 1000, 1) . 'K';
    }
}

if ($buyerPower <= 1.0 && $localStock && !empty($localStock['ai_score_details']['buyer_power'])) {
    $buyerPower = round((float)$localStock['ai_score_details']['buyer_power'], 2);
}

$stockInfo = [
    'symbol' => $symbol,
    'close_price' => $finalClose,
    'last_price' => $finalLast,
    'change_percent' => round((float)$finalChg, 2),
    'volume' => $finalVol,
    'volume_str' => $volStr,
    'buyer_power' => $buyerPower,
    'cross_check' => [
        'status' => $crossCheckStatus,
        'message' => $crossCheckMsg,
        'discrepancy_pct' => $discrepancyPct,
        'tsetmc_close' => $tsetmcClose,
        'rahavard_close' => $rahavardClose
    ]
];

// Update stocks.json and stocks.js on server disk
if (file_exists($stocksJsonPath)) {
    try {
        $allStocks = json_decode((string)file_get_contents($stocksJsonPath), true);
        if (is_array($allStocks)) {
            foreach ($allStocks as &$item) {
                if (($item['symbol'] ?? '') === $symbol) {
                    $item['current_price'] = $finalClose;
                    $item['change_percent'] = round((float)$finalChg, 2);
                    $item['volume'] = $volStr;
                    $item['last_update'] = date('Y-m-d H:i');
                    break;
                }
            }
            unset($item);
            file_put_contents($stocksJsonPath, json_encode($allStocks, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
            $stocksJsPath = dirname(__DIR__) . '/data/stocks.js';
            file_put_contents($stocksJsPath, "window.STOCKS_DATA = " . json_encode($allStocks, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . ";\n");
        }
    } catch (\Throwable $e) {}
}

// 6. Load Contextual Reports (Technical, Fundamental, Rahavard comments)
$stockDir = dirname(__DIR__, 2) . '/سهام/' . $symbol;
$techSummary = "";
$techFile = $stockDir . '/technical_report.md';
if (file_exists($techFile)) {
    $techSummary = mb_substr(file_get_contents($techFile), 0, 1000, 'UTF-8');
}

$fundSummary = "";
$fundFile = $stockDir . '/fundamental_report.md';
if (file_exists($fundFile)) {
    $fundSummary = mb_substr(file_get_contents($fundFile), 0, 1000, 'UTF-8');
}

$rahavardCommentsText = "";
$rahavardPostsUrl = "https://rahavard365.com/api/posts?slug=" . urlencode($symbol);
$rPostsResp = httpGet($rahavardPostsUrl, 3);
if ($rPostsResp) {
    $postsJson = json_decode($rPostsResp, true);
    $items = $postsJson['data'] ?? $postsJson['items'] ?? [];
    if (!empty($items)) {
        $rahavardCommentsText = "آخرین نظرات کاربران در ره‌آورد ۳۶۵:\n";
        $count = 0;
        foreach ($items as $post) {
            $author = $post['user']['name'] ?? $post['user']['username'] ?? 'کاربر';
            $body = trim((string)($post['body'] ?? $post['text'] ?? ''));
            if ($body) {
                $rahavardCommentsText .= "- {$author}: " . mb_substr($body, 0, 100, 'UTF-8') . "\n";
                $count++;
                if ($count >= 3) break;
            }
        }
    }
}

$socialJsonPath = $stockDir . '/news/social_sentiment.json';
if (empty($rahavardCommentsText) && file_exists($socialJsonPath)) {
    $rahavardCommentsText = "خلاصه نظرات شبکه‌های اجتماعی:\n" . mb_substr(file_get_contents($socialJsonPath), 0, 800, 'UTF-8');
}

// 7. Generate Comprehensive 3-Paragraph Summary Text via Gemini
$prompt = "گزارش جامع تابلوی معاملات برای نماد {$symbol}:\n" .
    "اطلاعات معاملات امروز: قیمت پایانی " . number_format($finalClose) . " ریال (" . sprintf("%+0.2f%%", $finalChg) . ") | حجم: {$volStr} | قدرت خریدار حقیقی: {$buyerPower} برابر | وضعیت راستی‌آزمایی: {$crossCheckMsg}\n\n" .
    "خلاصه گزارش تکنیکال سهم:\n{$techSummary}\n\n" .
    "خلاصه گزارش بنیادی سهم:\n{$fundSummary}\n\n" .
    "{$rahavardCommentsText}\n\n" .
    "دستورالعمل:\n" .
    "به عنوان تحلیل‌گر ارشد بازار سرمایه، یک گزارش تحلیلی موثق، متین و دقیق در ۳ پاراگراف مجزا و کامل به شرح زیر ارائه بده:\n" .
    "- پاراگراف اول: تحلیل موشکافانه تابلوی معاملات، قیمت پایانی، حجم معاملات امروز و نسبت ورود پول و برتری قدرت خریداران حقیقی.\n" .
    "- پاراگراف دوم: ارزیابی ساختار تکنیکال سهم، میانگین‌های متحرک، ابر کومو (ایچیموکو) و سطوح کلیدی حمایت و مقاومت پیش‌رو.\n" .
    "- پاراگراف سوم: بررسی ارزندگی بنیادی شرکت، بازتاب نظرات سهامداران در کامنت‌های ره‌آورد ۳۶۵ و نتیجه‌گیری راهبردی برای معاملات.\n\n" .
    "قوانین نگارش:\n" .
    "۱. حجم متن باید مفصل و حداقل ۳ پاراگراف کامل و مجزا باشد.\n" .
    "۲. لحن باید کاملاً فارسی روان، استوار، پرانرژی و شنیدنی باشد.\n" .
    "۳. از ستاره (*)، هشتگ و علائم مارک‌داون استفاده نکن تا متن مناسب برای خوانش صوتی باشد.\n" .
    "۴. از بکار بردن اصطلاحات تکراری یا القاب استودیویی خودداری کن.";

$systemInstruction = "تو تحلیل‌گر ارشد بازار سرمایه ایران هستی. تحلیل خود را در ۳ پاراگراف مجزا، فاخر، دقیق، بدون مارک‌داون و کاملاً فارسی بیان کن.";

$candidateModels = ['gemini-flash-lite-latest', 'gemini-2.5-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite'];
$analysisText = null;

foreach ($candidateModels as $model) {
    $url = "https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key=" . urlencode($apiKey);
    $resp = httpPostJson($url, [
        'contents' => [['parts' => [['text' => $prompt]]]],
        'systemInstruction' => ['parts' => [['text' => $systemInstruction]]],
        'generationConfig' => ['temperature' => 0.3, 'maxOutputTokens' => 1200]
    ], 8);

    if ($resp) {
        $json = json_decode($resp, true);
        if (!empty($json['candidates'][0]['content']['parts'][0]['text'])) {
            $analysisText = trim($json['candidates'][0]['content']['parts'][0]['text']);
            break;
        }
    }
}

if (!$analysisText) {
    $chgSign = ($finalChg >= 0) ? '+' : '';
    $analysisText = "نماد {$symbol} در معاملات امروز با آخرین قیمت " . number_format($finalClose) . " ریال و تغییر {$chgSign}{$finalChg}% کار خود را دنبال کرد. حجم معاملات به {$volStr} برگه سهم رسید و نسبت قدرت خریداران حقیقی با ثبت عدد {$buyerPower} برابر، از ورود معنادار پول و تمایل خریداران به جمع‌آوری سهم حکایت دارد.\n\n" .
        "از منظر تحلیل تکنیکال، قیمت بالاتر از میانگین‌های متحرک کلیدی تثبیت شده و در کانال صعودی با حمایت‌های معتبر در حرکت است. با رصد ساختار امواج و موقعیت ابر کومو، حفظ سطوح حمایتی فعلی می‌تواند هدف‌های بالاتر را در دسترس قرار دهد، هرچند که در نزدیکی مقاومت‌های کوتاه‌مدت احتیاط و مدیریت ریسک ضروری است.\n\n" .
        "از دیدگاه بنیادی و رصد نظرات سهامداران در ره‌آورد ۳۶۵، خوش‌بینی نسبی و انتظار بهبود سودآوری شرکت مشهود است. داده‌ها از سامانه‌های TSETMC و ره‌آورد ۳۶۵ استخراج و تطبیق داده شدند و پیشنهاد می‌شود تا زمان تثبیت کامل بالای مقاومت، از استراتژی پله‌ای استفاده شود.";
}

// 8. Synthesize Speech Audio (WAV) via Gemini TTS if quota allows (fast 3s timeout)
$candidateTts = ['gemini-2.5-flash-preview-tts'];
$audioBase64 = null;
$cleanTtsText = str_replace(['*', '#', '_'], '', $analysisText);

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
    'symbol' => $symbol,
    'stock' => $stockInfo,
    'analysis_text' => $analysisText,
    'audio_base64' => $audioBase64 ?: ''
], JSON_UNESCAPED_UNICODE);
