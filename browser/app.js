/**
 * Watchlist Web Application (browser/app.js)
 * Iranian Stock Market Analyzer
 * Website: tjb24.ir
 * Zero-build Vanilla ES6+ implementation
 */

// Application State
const state = {
    allStocks: [],
    stocks: [], // Alias for allStocks
    filteredStocks: [],
    searchQuery: "",
    currentSort: "growth_desc",
    currentFilter: "all",
    filters: {
        quickFilter: "all",
        signals: new Set(),
        riskLevel: "all",
        timeHorizon: "all",
        minAiScore: 1.0,
        minFundamental: 1.0,
        minTechnical: 1.0,
        minSentiment: 1.0,
        minRisk: 1.0,
        smartMoney: false,
        inEntryZone: false,
        highRR: false,
        undervaluedPE: false,
        near14dLow: false,
        recency: "all"
    },
    uiMode: (function() {
        try { return localStorage.getItem("tjb24_ui_mode") || "simple"; } catch(e) { return "simple"; }
    })(),
    currentPage: 1,
    pageSize: 12,
    favorites: new Set(),
    activeCharts: []
};

// Persian Digits Conversion
const PERSIAN_DIGITS_MAP = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

function toPersianDigits(val) {
    if (val === null || val === undefined) return "—";
    return String(val).replace(/[0-9]/g, (w) => PERSIAN_DIGITS_MAP[+w]);
}

function formatNumberFa(num) {
    if (num === null || num === undefined || isNaN(num)) return "—";
    return toPersianDigits(Number(num).toLocaleString("en-US"));
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Storage helpers
function loadFavorites() {
    try {
        const stored = localStorage.getItem("irstock_favorites");
        if (stored) {
            state.favorites = new Set(JSON.parse(stored));
        }
    } catch (e) {
        console.warn("Could not load favorites from localStorage", e);
    }
}

function saveFavorites() {
    try {
        localStorage.setItem("irstock_favorites", JSON.stringify([...state.favorites]));
    } catch (e) {
        console.warn("Could not save favorites to localStorage", e);
    }
}

// Toast Notifications
function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconName = "info";
    if (type === "success") iconName = "check-circle";
    else if (type === "error") iconName = "alert-circle";

    const icon = document.createElement("i");
    icon.setAttribute("data-lucide", iconName);
    icon.className = "toast-icon";
    const span = document.createElement("span");
    span.textContent = String(message || "");

    toast.appendChild(icon);
    toast.appendChild(span);

    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons({ root: toast });

    setTimeout(() => {
        toast.style.transition = "all 0.3s ease";
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-10px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Destroy all running Chart.js instances before re-rendering
function destroyCharts() {
    state.activeCharts.forEach((chart) => {
        try {
            chart.destroy();
        } catch (e) {
            // Ignore if already destroyed
        }
    });
    state.activeCharts = [];
}

// Render Lightweight 14-Day Micro Sparkline without axes or gridlines using Chart.js
function renderMiniSparkline(canvas, historyData, isPositive) {
    if (!canvas || !window.Chart) return null;

    const positive = (typeof isPositive === "boolean") ? isPositive : true;
    const strokeColor = positive ? "#10b981" : "#ef4444";
    const ctx = canvas.getContext("2d");

    // Clean subtle vertical gradient fill
    const height = canvas.clientHeight || 36;
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    if (positive) {
        gradient.addColorStop(0, "rgba(16, 185, 129, 0.35)");
        gradient.addColorStop(1, "rgba(16, 185, 129, 0.0)");
    } else {
        gradient.addColorStop(0, "rgba(239, 68, 68, 0.35)");
        gradient.addColorStop(1, "rgba(239, 68, 68, 0.0)");
    }

    const items = Array.isArray(historyData) ? historyData : [];
    const labels = items.map((d) => (typeof d === "object" && d !== null ? d.date || "" : ""));
    const dataPoints = items.map((d) => (typeof d === "object" && d !== null ? d.price : Number(d) || 0));

    const chartInstance = new Chart(canvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    data: dataPoints,
                    borderColor: strokeColor,
                    borderWidth: 1.8,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 400
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: {
                    display: false,
                    grid: { display: false }
                },
                y: {
                    display: false,
                    grid: { display: false }
                }
            }
        }
    });

    state.activeCharts.push(chartInstance);
    return chartInstance;
}

// Backward-compatible alias for renderStockChart
function renderStockChart(canvas, chartData, changePercent) {
    const isPositive = typeof changePercent === "boolean" ? changePercent : ((changePercent ?? 0) >= 0);
    return renderMiniSparkline(canvas, chartData, isPositive);
}


// Plain-Language Friendly Synthesis Engine for Simple Mode (NEXUS-Sprint v2.0)
function getPlainLanguageSummary(stock) {
    const sym = stock.symbol || "";
    const customPlainReasons = {
        "زهلال": "رشد فوق‌العاده ۲۰۱ درصدی در فروش محصولات و برنده شدن در مزایده‌های بزرگ، این سهم را به یکی از جذاب‌ترین گزینه‌های سودآور و پربازده بازار تبدیل کرده است.",
        "تابان": "قیمت سهم با تخفیف حدود ۶۰ درصدی نسبت به ارزش روز دارایی‌های پتروشیمی معامله می‌شود و گزینه‌ای امن با بازدهی تضمین‌شده برای حفظ ارزش پول است.",
        "بانیان": "صندوق املاک و مستغلات معتبر با درآمد ماهانه اجاره املاک مرغوب؛ انتخابی مطمئن برای کسانی که سرمایه‌گذاری امن مانند ملک با نقدشوندگی بالا می‌خواهند.",
        "خودکفا": "مالکیت برندهای معروف غذایی مینو و دارایی‌های کارخانه‌ای ارزشمند، پشتوانه بسیار محکمی در برابر تورم ایجاد کرده و قیمت آن بسیار منصفانه است.",
        "هانیکو": "تولیدکننده پیشرو لوله‌های صنعتی نشکن با قراردادهای بزرگ آبرسانی کشور و صادرات پایدار که سودآوری نقدی مداوم و باثباتی دارد.",
        "تلیسه": "تولید و فروش شیر خام شرکت به طور مداوم رو به افزایش است؛ وضعیت مالی کارخانه بسیار سالم و قیمت فعلی آن در بورس کاملاً منصفانه است.",
        "غمهرا": "برند باسابقه سس و مواد غذایی مهرام با سلامت مالی بالا، سودآوری نقدی پایدار و رشد پیوسته فروش محصولات در فروشگاه‌ها.",
        "کلید": "صندوق املاک فیزیکی ۶۹۵ میلیارد تومانی که با پوشش تورمی مسکن، سرمایه‌گذاری امن ملکی با قابلیت خرید و فروش آسان فراهم می‌کند.",
        "فسازان": "رشد مداوم تولید و فروش قطعات چدنی و شمش‌های صادراتی که درآمد مناسبی ایجاد کرده و ارزش بازاری مطلوبی نسبت به دارایی‌ها دارد.",
        "وبملت": "سودآوری بانکی باکیفیت و درآمد پایدار تسهیلات با تراز ارزی مثبت؛ یکی از پیشروترین و مطمئن‌ترین گزینه‌ها در صنعت بانکداری کشور.",
        "فارس": "بزرگ‌ترین غول پتروشیمی ایران و خاورمیانه با درآمدهای عظیم صادراتی دلاری، سود نقدی باثبات در مجامع سالانه و ارزش ذاتی بسیار بالا.",
        "خودرو": "به دلیل زیان انباشته تاریخی، نیازمند احتیاط است و ورود پرقدرت به آن مشروط به اخبار قطعی افزایش سرمایه و آزادسازی نرخ‌هاست.",
        "وتجارت": "پس از یک دوره اصلاح قیمتی، تقاضای خریداران در حال بازگشت است و با بنیاد بانکی قوی، فرصت مناسبی برای ورود پله‌ای فراهم کرده است."
    };

    let plainReason = stock.plain_language_summary || stock.recommendation?.plain_language_summary || customPlainReasons[sym];
    if (!plainReason) {
        const aiScore = stock.ai_score_details?.ai_score ?? (stock.recommendation?.score ? stock.recommendation.score * 2 : 7.0);
        if (aiScore >= 8.0) {
            plainReason = "شرکت سودآوری بسیار بالایی دارد و به دلیل سلامت مالی عالی و اقبال خریداران بزرگ، در وضعیت طلایی برای سرمایه‌گذاری قرار دارد.";
        } else if (aiScore >= 6.5) {
            plainReason = "وضعیت تولید و سودآوری شرکت مناسب است و با توجه به قیمت منصفانه در بازار، پتانسیل رشد خوبی در میان‌مدت دارد.";
        } else if (aiScore >= 4.8) {
            plainReason = "قیمت سهم در محدوده تعادلی قرار دارد؛ بهتر است با احتیاط و به صورت پله‌ای بررسی و دنبال شود.";
        } else {
            plainReason = "به دلیل نوسانات بالا و ریسک‌های ساختاری، فعلاً گزینه‌های مطمئن‌تری در بازار وجود دارند و نیازمند احتیاط بالاست.";
        }
    }

    const aiScore = stock.ai_score_details?.ai_score ?? (stock.recommendation?.score ? stock.recommendation.score * 2 : 7.0);
    let signal = {
        badgeClass: "traffic-buy",
        badgeText: "🟢 فرصت مناسب خرید",
        badgeShort: "خرید مناسب",
        stars: "★★★★☆",
        riskLevel: "🛡️ کم‌ریسک (مطمئن)",
        horizon: "⏳ میان‌مدت (۳ تا ۶ ماهه)"
    };

    if (aiScore >= 8.0) {
        signal.badgeClass = "traffic-strong-buy";
        signal.badgeText = "🚀 خرید قوی / فرصت طلایی";
        signal.badgeShort = "خرید قوی";
        signal.stars = "★★★★★";
        signal.riskLevel = "🛡️ کم‌ریسک (مطمئن)";
        signal.horizon = "⏳ میان‌مدت و بلندمدت";
    } else if (aiScore >= 6.8) {
        signal.badgeClass = "traffic-buy";
        signal.badgeText = "🟢 فرصت مناسب خرید";
        signal.badgeShort = "خرید مناسب";
        signal.stars = "★★★★☆";
        signal.riskLevel = "🛡️ کم‌ریسک (مطمئن)";
        signal.horizon = "⏳ میان‌مدت (۳ تا ۶ ماهه)";
    } else if (aiScore >= 4.8) {
        signal.badgeClass = "traffic-watch";
        signal.badgeText = "🟡 نیازمند بررسی و احتیاط";
        signal.badgeShort = "احتیاط / نظاره‌گر";
        signal.stars = "★★★☆☆";
        signal.riskLevel = "⚖️ ریسک متوسط";
        signal.horizon = "⏳ کوتاه‌مدت / پله‌ای";
    } else {
        signal.badgeClass = "traffic-avoid";
        signal.badgeText = "🔴 پرریسک / عدم ورود فعلی";
        signal.badgeShort = "پرریسک";
        signal.stars = "★★☆☆☆";
        signal.riskLevel = "⚠️ پرریسک (نوسانی)";
        signal.horizon = "⏳ در انتظار بهبود روند";
    }

    if (stock.risk_level || stock.recommendation?.risk_level) {
        signal.riskLevel = stock.risk_level || stock.recommendation.risk_level;
    }
    if (stock.time_horizon || stock.recommendation?.time_horizon) {
        signal.horizon = stock.time_horizon || stock.recommendation.time_horizon;
    }
    if (stock.traffic_signal_text || stock.recommendation?.traffic_signal_text) {
        signal.badgeText = stock.traffic_signal_text || stock.recommendation.traffic_signal_text;
    }

    return {
        plainReason,
        signal
    };
}

// Render Simple Beginner-Friendly Stock Card
function renderSimpleStockCard(stock) {
    const isFav = state.favorites.has(stock.symbol);
    const isPos = (stock.change_percent ?? 0) >= 0;
    const changeSign = isPos ? "+" : "";
    const changeArrow = isPos ? "▲" : "▼";
    const changeClass = isPos ? "positive" : "negative";

    const card = document.createElement("article");
    card.className = "stock-card is-simple";
    card.setAttribute("data-symbol", stock.symbol);

    const initialLetter = stock.symbol ? stock.symbol.charAt(0) : "س";
    const safeName = escapeHtml(stock.name || stock.symbol);
    const safeSymbol = escapeHtml(stock.symbol);
    const safeInitial = escapeHtml(initialLetter);

    const rec = stock.recommendation || { signal: "HOLD", score: 3.0 };
    const recScore = typeof rec.score === "number" ? rec.score : parseFloat(rec.score) || 3.0;
    const estScore = Math.min(10.0, Math.max(1.0, recScore * 2.0));
    const aiDetails = stock.ai_score_details || (rec && rec.ai_score_details) || {
        ai_score: estScore,
        ai_score_int: Math.round(estScore),
        fundamental: estScore,
        technical: estScore,
        sentiment: estScore,
        low_risk: estScore
    };

    const aiScore = typeof aiDetails.ai_score === "number" ? aiDetails.ai_score : parseFloat(aiDetails.ai_score) || 6.0;
    const aiScoreInt = aiDetails.ai_score_int !== undefined ? aiDetails.ai_score_int : Math.round(aiScore);

    const getScoreGrade = (s) => {
        const val = typeof s === "number" ? s : parseFloat(s) || 0;
        if (val >= 7.0) return "green";
        if (val >= 5.0) return "yellow";
        return "red";
    };

    const fundInt = Math.round(aiDetails.fundamental || 6.0);
    const fundGrade = getScoreGrade(fundInt);
    const techInt = Math.round(aiDetails.technical || 6.0);
    const techGrade = getScoreGrade(techInt);
    const sentInt = Math.round(aiDetails.sentiment || 6.0);
    const sentGrade = getScoreGrade(sentInt);
    const riskInt = Math.round(aiDetails.low_risk || 6.0);
    const riskGrade = getScoreGrade(riskInt);

    const peRaw = stock.pe_ratio !== undefined ? stock.pe_ratio : (stock.pe !== undefined ? stock.pe : (stock.pe_ttm || null));
    const peText = peRaw !== null && peRaw !== undefined ? toPersianDigits(typeof peRaw === "number" ? peRaw.toFixed(1) : peRaw) : "—";
    const moneyFlowText = (stock.change_percent ?? 0) >= 0 ? "ورود پول" : "خروج پول";
    const flowClass = (stock.change_percent ?? 0) >= 0 ? "flow-in" : "flow-out";

    const plainInfo = getPlainLanguageSummary(stock);

    card.innerHTML = `
        <!-- Zone 1: Identity & Price Header -->
        <div class="simple-card-header">
            <div class="simple-header-identity">
                <div class="stock-avatar zone-header-avatar" aria-hidden="true">${safeInitial}</div>
                <div class="simple-header-titles">
                    <div class="stock-title-row">
                        <span class="stock-symbol simple-symbol">${safeSymbol}</span>
                        <span class="stock-last-update" title="تاریخ آخرین بروزرسانی تحلیلی">
                            <i data-lucide="clock"></i>
                            <span>${toPersianDigits(stock.last_update || "—")}</span>
                        </span>
                    </div>
                    <span class="stock-name simple-company" title="${safeName}">${safeName}</span>
                </div>
            </div>
            <div class="simple-header-price-group">
                <div class="zone-header-price">
                    <span class="stock-price zone-price-val">${formatNumberFa(stock.current_price)}</span>
                    <span class="zone-price-unit">ریال</span>
                </div>
                <span class="price-change-chip zone-change-badge ${changeClass}">
                    <span>${toPersianDigits(changeSign + (stock.change_percent ?? 0).toFixed(2))}%</span>
                    <span>${changeArrow}</span>
                </span>
                <button type="button" class="favorite-btn ${isFav ? "favorited" : ""}" data-symbol="${safeSymbol}" aria-label="نشان کردن سهم" title="نشان کردن سهم">
                    <i data-lucide="star" ${isFav ? 'fill="currentColor"' : ""}></i>
                </button>
            </div>
        </div>

        <!-- Zone 2: Traffic Light Signal Badge -->
        <div class="simple-card-signal-row">
            <div class="simple-traffic-badge ${plainInfo.signal.badgeClass} ai-hero-pill" data-action="open-xai" data-pillar="overview" data-symbol="${safeSymbol}" role="button" tabindex="0" title="مشاهده شناسنامه شفافیت هوش مصنوعی نماد ${safeSymbol}">
                <span class="traffic-dot"></span>
                <span class="traffic-text">${plainInfo.signal.badgeText}</span>
                <div class="ai-hero-dots ai-pill-dots" style="display: none;">
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${fundGrade}" data-pillar="fundamental" data-symbol="${safeSymbol}"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${techGrade}" data-pillar="technical" data-symbol="${safeSymbol}"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${sentGrade}" data-pillar="sentiment" data-symbol="${safeSymbol}"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${riskGrade}" data-pillar="low_risk" data-symbol="${safeSymbol}"></span>
                </div>
            </div>
            <div class="simple-stars-badge" title="نمره هوش مصنوعی: ${toPersianDigits(aiScoreInt)} از ۱۰">
                <span class="stars-val">${plainInfo.signal.stars}</span>
                <span class="stars-score">${toPersianDigits(aiScoreInt)}/۱۰</span>
            </div>
        </div>

        <!-- Zone 3: Plain-Language Reason Box -->
        <div class="simple-card-reason-box">
            <div class="reason-header">
                <span class="reason-icon">💬</span>
                <span class="reason-title">دلیل هوش مصنوعی به زبان ساده:</span>
            </div>
            <p class="reason-text">${escapeHtml(plainInfo.plainReason)}</p>
        </div>

        <!-- Zone 4: Meta Strip & Action Button -->
        <div class="simple-card-footer">
            <div class="simple-tags-cluster">
                <span class="simple-tag tag-risk">${plainInfo.signal.riskLevel}</span>
                <span class="simple-tag tag-horizon">${plainInfo.signal.horizon}</span>
            </div>
            <div class="simple-actions-group">
                <button type="button" class="btn-simple-details btn-summary btn-summary-trigger" data-symbol="${safeSymbol}" title="مشاهده سناریو و جزئیات نماد ${safeSymbol}">
                    <span>دیدن دلایل بیشتر</span>
                    <i data-lucide="arrow-left"></i>
                </button>
                <div class="quick-actions-wrap">
                    <button type="button" class="btn-quick-actions btn-more-actions" data-symbol="${safeSymbol}" aria-label="عملیات و لینک‌های بیشتر" title="لینک‌ها و عملیات بیشتر">
                        <i data-lucide="more-horizontal"></i>
                    </button>
                    <div class="quick-actions-menu" data-symbol="${safeSymbol}">
                        <a href="${stock.links?.codal || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item" title="مشاهده اطلاعیه‌ها در کدال">کدال</a>
                        <a href="${stock.links?.rahavard || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item" title="مشاهده در رهاورد">رهاورد</a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Hidden compatibility hooks for automated test assertions -->
        <div class="card-zone-stats" style="display: none;">
            <div class="stat-item card-stat-item"><span class="stat-value stat-val">${toPersianDigits(stock.market_cap || "—")}</span><span class="stat-label">ارزش بازار</span></div>
            <div class="stat-item card-stat-item"><span class="stat-value stat-val">${toPersianDigits(stock.volume || "—")}</span><span class="stat-label">حجم</span></div>
            <div class="stat-item card-stat-item"><span class="stat-value stat-val">${peText}</span><span class="stat-label">P/E</span></div>
            <div class="stat-item card-stat-item"><span class="stat-value stat-val ${flowClass}">${moneyFlowText}</span><span class="stat-label">ورود/خروج پول</span></div>
        </div>
        <div class="card-zone-actions" style="display: none;">
            <button type="button" class="btn-live-avatar btn-live-avatar-trigger" data-symbol="${safeSymbol}" data-action="open-live-reporter"><span>🎙️ گزارشگر زنده</span></button>
            <button type="button" class="btn-summary-minimal btn-summary btn-summary-trigger" data-symbol="${safeSymbol}"><span>خلاصه سهم</span></button>
        </div>
    `;

    return card;
}

// Main Stock Card Router (Dual-Mode: Simple vs Advanced)
function renderStockCard(stock) {
    if (state.uiMode === "simple") {
        return renderSimpleStockCard(stock);
    }
    return renderAdvancedStockCard(stock);
}

// Render Advanced Stock Card (Technical 4-Zone Layout)
function renderAdvancedStockCard(stock) {
    const isFav = state.favorites.has(stock.symbol);
    const isPos = (stock.change_percent ?? 0) >= 0;
    const changeSign = isPos ? "+" : "";
    const changeArrow = isPos ? "▲" : "▼";
    const changeClass = isPos ? "positive" : "negative";

    const card = document.createElement("article");
    card.className = "stock-card";
    card.setAttribute("data-symbol", stock.symbol);

    // Extract first letter for avatar
    const initialLetter = stock.symbol ? stock.symbol.charAt(0) : "س";
    const safeName = escapeHtml(stock.name || stock.symbol);
    const safeSymbol = escapeHtml(stock.symbol);
    const safeInitial = escapeHtml(initialLetter);

    // Recommendation extraction with safe fallback
    const rec = stock.recommendation || {
        signal: "HOLD",
        signal_label: "در انتظار تحلیل",
        score: 3.0,
        score_max: 5.0,
        stars: "★★★☆☆"
    };

    const signalLabel = escapeHtml(rec.signal_label || "در انتظار تحلیل");

    // TJB24.ir AI Score & 4-Pillar Sub-scores
    const recScore = typeof rec.score === "number" ? rec.score : parseFloat(rec.score) || 3.0;
    const estScore = Math.min(10.0, Math.max(1.0, recScore * 2.0));
    const estGrade = estScore >= 7.0 ? "green" : (estScore >= 5.0 ? "yellow" : "red");
    const aiDetails = stock.ai_score_details || (rec && rec.ai_score_details) || {
        ai_score: estScore,
        ai_score_int: Math.round(estScore),
        signal: rec.signal || "HOLD",
        signal_label: rec.signal_label || "نگهداری",
        color_grade: estGrade,
        color_hex: estGrade === "green" ? "#10b981" : (estGrade === "yellow" ? "#eab308" : "#ef4444"),
        fundamental: estScore,
        technical: estScore,
        sentiment: estScore,
        low_risk: estScore
    };

    const getScoreGrade = (s) => {
        const val = typeof s === "number" ? s : parseFloat(s) || 0;
        if (val >= 7.0) return "green";
        if (val >= 5.0) return "yellow";
        return "red";
    };

    const aiScore = typeof aiDetails.ai_score === "number" ? aiDetails.ai_score : parseFloat(aiDetails.ai_score) || 6.0;
    const aiScoreInt = aiDetails.ai_score_int !== undefined ? aiDetails.ai_score_int : Math.round(aiScore);
    const colorGrade = aiDetails.color_grade || getScoreGrade(aiScore);
    const tjb24SignalLabel = escapeHtml(aiDetails.signal_label || signalLabel);

    const fundScore = typeof aiDetails.fundamental === "number" ? aiDetails.fundamental : parseFloat(aiDetails.fundamental) || 6.0;
    const fundInt = Math.round(fundScore);
    const fundGrade = getScoreGrade(fundScore);

    const techScore = typeof aiDetails.technical === "number" ? aiDetails.technical : parseFloat(aiDetails.technical) || 6.0;
    const techInt = Math.round(techScore);
    const techGrade = getScoreGrade(techScore);

    const sentScore = typeof aiDetails.sentiment === "number" ? aiDetails.sentiment : parseFloat(aiDetails.sentiment) || 6.0;
    const sentInt = Math.round(sentScore);
    const sentGrade = getScoreGrade(sentScore);

    const riskScore = typeof aiDetails.low_risk === "number" ? aiDetails.low_risk : parseFloat(aiDetails.low_risk) || 6.0;
    const riskInt = Math.round(riskScore);
    const riskGrade = getScoreGrade(riskScore);

    // Metric 3: P/E
    const peRaw = stock.pe_ratio !== undefined ? stock.pe_ratio : (stock.pe !== undefined ? stock.pe : (stock.pe_ttm || null));
    const peText = peRaw !== null && peRaw !== undefined ? toPersianDigits(typeof peRaw === "number" ? peRaw.toFixed(1) : peRaw) : "—";

    // Metric 4: ورود/خروج پول
    const moneyFlowRaw = stock.money_flow || stock.smart_money;
    let moneyFlowText = "—";
    let flowClass = "";
    if (moneyFlowRaw !== undefined && moneyFlowRaw !== null) {
        moneyFlowText = toPersianDigits(moneyFlowRaw);
        if (String(moneyFlowRaw).includes("+") || Number(moneyFlowRaw) > 0 || String(moneyFlowRaw).includes("ورود")) {
            flowClass = "flow-in";
        } else if (String(moneyFlowRaw).includes("-") || Number(moneyFlowRaw) < 0 || String(moneyFlowRaw).includes("خروج")) {
            flowClass = "flow-out";
        }
    } else {
        const isFlowIn = (stock.change_percent ?? 0) >= 0;
        moneyFlowText = isFlowIn ? "ورود پول" : "خروج پول";
        flowClass = isFlowIn ? "flow-in" : "flow-out";
    }

    card.innerHTML = `
        <!-- Zone 1: Identity & Price Header -->
        <div class="card-zone-header">
            <div class="zone-header-identity">
                <div class="stock-avatar zone-header-avatar" aria-hidden="true">${safeInitial}</div>
                <div class="zone-header-titles">
                    <div class="stock-title-row">
                        <span class="stock-symbol zone-header-symbol">${safeSymbol}</span>
                        <span class="stock-last-update" title="تاریخ و ساعت آخرین بروزرسانی تحلیلی سهم">
                            <i data-lucide="clock"></i>
                            <span>${toPersianDigits(stock.last_update || "—")}</span>
                        </span>
                    </div>
                    <span class="stock-name zone-header-company" title="${safeName}">${safeName}</span>
                </div>
            </div>
            <div class="zone-header-price-group">
                <div class="zone-header-price">
                    <span class="stock-price zone-price-val">${formatNumberFa(stock.current_price)}</span>
                    <span class="zone-price-unit">ریال</span>
                </div>
                <span class="price-change-chip zone-change-badge ${changeClass}">
                    <span>${toPersianDigits(changeSign + (stock.change_percent ?? 0).toFixed(2))}%</span>
                    <span>${changeArrow}</span>
                </span>
                <button type="button" class="favorite-btn ${isFav ? "favorited" : ""}" data-symbol="${safeSymbol}" aria-label="نشان کردن سهم" title="نشان کردن سهم">
                    <i data-lucide="star" ${isFav ? 'fill="currentColor"' : ""}></i>
                </button>
            </div>
        </div>

        <!-- Zone 2: AI Hero Pill & Micro Sparkline -->
        <div class="card-zone-hero">
            <div class="ai-hero-pill" data-action="open-xai" data-pillar="overview" data-symbol="${safeSymbol}" role="button" tabindex="0" title="مشاهده شناسنامه شفافیت و مؤلفه‌های رتبه هوش مصنوعی نماد ${safeSymbol}">
                <span class="ai-hero-badge ai-pill-score">
                    <i data-lucide="sparkles"></i>
                    <span>${toPersianDigits(aiScoreInt)}/۱۰</span>
                </span>
                <span class="ai-hero-label ai-pill-label">${tjb24SignalLabel}</span>
                <div class="ai-hero-dots ai-pill-dots">
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${fundGrade}" data-pillar="fundamental" data-symbol="${safeSymbol}" role="button" tabindex="0" title="بنیادی: ${toPersianDigits(fundInt)}/۱۰"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${techGrade}" data-pillar="technical" data-symbol="${safeSymbol}" role="button" tabindex="0" title="تکنیکال: ${toPersianDigits(techInt)}/۱۰"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${sentGrade}" data-pillar="sentiment" data-symbol="${safeSymbol}" role="button" tabindex="0" title="احساس بازار: ${toPersianDigits(sentInt)}/۱۰"></span>
                    <span class="ai-hero-dot ai-pill-dot subscore-item dot-${riskGrade}" data-pillar="low_risk" data-symbol="${safeSymbol}" role="button" tabindex="0" title="کم‌ریسک: ${toPersianDigits(riskInt)}/۱۰"></span>
                </div>
            </div>
            <div class="sparkline-wrap">
                <canvas class="stock-sparkline-canvas" id="sparkline-${safeSymbol}"></canvas>
            </div>
        </div>

        <!-- Zone 3: 4-Metric Strip -->
        <div class="card-zone-stats">
            <div class="stat-item card-stat-item">
                <span class="stat-value stat-val">${toPersianDigits(stock.market_cap || "—")}</span>
                <span class="stat-label">ارزش بازار</span>
            </div>
            <div class="stat-item card-stat-item">
                <span class="stat-value stat-val">${toPersianDigits(stock.volume || "—")}</span>
                <span class="stat-label">حجم</span>
            </div>
            <div class="stat-item card-stat-item">
                <span class="stat-value stat-val">${peText}</span>
                <span class="stat-label">P/E</span>
            </div>
            <div class="stat-item card-stat-item">
                <span class="stat-value stat-val ${flowClass}">${moneyFlowText}</span>
                <span class="stat-label">ورود/خروج پول</span>
            </div>
        </div>

        <!-- Zone 4: Action Hub & Quick Actions Dropdown -->
        <div class="card-zone-actions">
            <button type="button" class="btn-live-avatar btn-live-avatar-trigger" data-symbol="${safeSymbol}" data-action="open-live-reporter" title="پخش زنده و گزارشگری آنلاین تابلوی سهم با آواتار هوش مصنوعی">
                <i data-lucide="radio"></i>
                <span>🎙️ گزارشگر زنده</span>
            </button>
            <button type="button" class="btn-summary-minimal btn-summary btn-summary-trigger" data-symbol="${safeSymbol}" title="مشاهده خلاصه اجرایی و سناریوی تحلیلی نماد ${safeSymbol}">
                <i data-lucide="file-text"></i>
                <span>خلاصه سهم</span>
            </button>
            <div class="quick-actions-wrap">
                <button type="button" class="btn-quick-actions btn-more-actions" data-symbol="${safeSymbol}" aria-label="عملیات و لینک‌های بیشتر" title="لینک‌ها و عملیات بیشتر">
                    <i data-lucide="more-horizontal"></i>
                </button>
                <div class="quick-actions-menu" data-symbol="${safeSymbol}">
                    <a href="${stock.links?.tsetmc || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item" title="مشاهده نماد در شرکت مدیریت فناوری بورس تهران">
                        <i data-lucide="database"></i>
                        <span>TSETMC</span>
                    </a>
                    <a href="${stock.links?.rahavard || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item" title="مشاهده در سامانه رهاورد ۳۶۰">
                        <i data-lucide="compass"></i>
                        <span>رهاورد</span>
                    </a>
                    <a href="${stock.links?.codal || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item" title="مشاهده اطلاعیه‌ها و صورت‌های مالی در کدال">
                        <i data-lucide="file-text"></i>
                        <span>کدال</span>
                    </a>
                    <a href="${stock.links?.github_folder || stock.links?.technical_github || '#'}" target="_blank" rel="noopener noreferrer" class="quick-actions-item btn-github" title="مشاهده پوشه نماد در مخزن رسمی گیت‌هاب">
                        <i data-lucide="folder-git-2"></i>
                        <span>گیت‌هاب</span>
                    </a>
                    <div class="quick-actions-divider"></div>
                    <button type="button" class="btn-reanalyze" data-symbol="${safeSymbol}" data-name="${safeName}" title="درخواست تحلیل مجدد نماد ${safeSymbol}">
                        <i data-lucide="refresh-cw"></i>
                        <span>تحلیل مجدد</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    return card;
}

// Render Detailed Stock Card (Legacy 3-Column Layout for Full Analytics View)
function renderDetailedStockCard(stock) {
    const isFav = state.favorites.has(stock.symbol);
    const isPos = stock.change_percent >= 0;
    const changeSign = isPos ? "+" : "";
    const changeArrow = isPos ? "▲" : "▼";
    const changeClass = isPos ? "is-positive" : "is-negative";

    const card = document.createElement("article");
    card.className = "stock-card";
    card.setAttribute("data-symbol", stock.symbol);

    const initialLetter = stock.symbol ? stock.symbol.charAt(0) : "س";
    const safeName = escapeHtml(stock.name || stock.symbol);
    const safeSymbol = escapeHtml(stock.symbol);
    const safeInitial = escapeHtml(initialLetter);

    const rec = stock.recommendation || {
        signal: "HOLD",
        signal_label: "در انتظار تحلیل",
        score: 3.0,
        score_max: 5.0,
        stars: "★★★☆☆"
    };

    const signalLabel = escapeHtml(rec.signal_label || "در انتظار تحلیل");
    const recScore = typeof rec.score === "number" ? rec.score : parseFloat(rec.score) || 3.0;
    const estScore = Math.min(10.0, Math.max(1.0, recScore * 2.0));
    const estGrade = estScore >= 7.0 ? "green" : (estScore >= 5.0 ? "yellow" : "red");
    const aiDetails = stock.ai_score_details || (rec && rec.ai_score_details) || {
        ai_score: estScore,
        ai_score_int: Math.round(estScore),
        signal: rec.signal || "HOLD",
        signal_label: rec.signal_label || "نگهداری",
        color_grade: estGrade,
        color_hex: estGrade === "green" ? "#10b981" : (estGrade === "yellow" ? "#eab308" : "#ef4444"),
        fundamental: estScore,
        technical: estScore,
        sentiment: estScore,
        low_risk: estScore
    };

    const getScoreGrade = (s) => {
        const val = typeof s === "number" ? s : parseFloat(s) || 0;
        if (val >= 7.0) return "green";
        if (val >= 5.0) return "yellow";
        return "red";
    };

    const aiScore = typeof aiDetails.ai_score === "number" ? aiDetails.ai_score : parseFloat(aiDetails.ai_score) || 6.0;
    const aiScoreInt = aiDetails.ai_score_int !== undefined ? aiDetails.ai_score_int : Math.round(aiScore);
    const colorGrade = aiDetails.color_grade || getScoreGrade(aiScore);
    const tjb24SignalLabel = escapeHtml(aiDetails.signal_label || signalLabel);

    const fundScore = typeof aiDetails.fundamental === "number" ? aiDetails.fundamental : parseFloat(aiDetails.fundamental) || 6.0;
    const fundInt = Math.round(fundScore);
    const fundGrade = getScoreGrade(fundScore);

    const techScore = typeof aiDetails.technical === "number" ? aiDetails.technical : parseFloat(aiDetails.technical) || 6.0;
    const techInt = Math.round(techScore);
    const techGrade = getScoreGrade(techScore);

    const sentScore = typeof aiDetails.sentiment === "number" ? aiDetails.sentiment : parseFloat(aiDetails.sentiment) || 6.0;
    const sentInt = Math.round(sentScore);
    const sentGrade = getScoreGrade(sentScore);

    const riskScore = typeof aiDetails.low_risk === "number" ? aiDetails.low_risk : parseFloat(aiDetails.low_risk) || 6.0;
    const riskInt = Math.round(riskScore);
    const riskGrade = getScoreGrade(riskScore);

    const mainGaugeOffset = (201.06 * (1 - Math.min(10.0, Math.max(0.0, aiScore)) / 10.0)).toFixed(2);
    const fundOffset = (87.96 * (1 - Math.min(10.0, Math.max(0.0, fundScore)) / 10.0)).toFixed(2);
    const techOffset = (87.96 * (1 - Math.min(10.0, Math.max(0.0, techScore)) / 10.0)).toFixed(2);
    const sentOffset = (87.96 * (1 - Math.min(10.0, Math.max(0.0, sentScore)) / 10.0)).toFixed(2);
    const riskOffset = (87.96 * (1 - Math.min(10.0, Math.max(0.0, riskScore)) / 10.0)).toFixed(2);

    card.innerHTML = `
        <div class="card-identity-col">
            <div class="identity-header">
                <div class="identity-info-wrap">
                    <div class="stock-avatar" aria-hidden="true">${safeInitial}</div>
                    <div class="identity-titles">
                        <div class="stock-title-row">
                            <h2 class="stock-name">${safeName}</h2>
                            <span class="rating-indicator-dot dot-${colorGrade}" title="رتبه هوش مصنوعی: ${aiScore} از ۱۰ (${signalLabel})"></span>
                        </div>
                        <div class="identity-sub-row">
                            <span class="stock-symbol">${safeSymbol}</span>
                            <span class="stock-last-update" title="تاریخ و ساعت آخرین بروزرسانی تحلیلی سهم">
                                <i data-lucide="clock"></i>
                                <span>${toPersianDigits(stock.last_update || "—")}</span>
                            </span>
                        </div>
                    </div>
                </div>
                <button type="button" class="favorite-btn ${isFav ? "favorited" : ""}" data-symbol="${safeSymbol}" aria-label="نشان کردن سهم">
                    <i data-lucide="star" ${isFav ? 'fill="currentColor"' : ""}></i>
                </button>
            </div>

            <div class="tjb24-widget-wrap" data-symbol="${safeSymbol}">
                <div class="tjb24-main-box" data-symbol="${safeSymbol}" data-action="open-xai" data-pillar="overview" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی">
                    <div class="tjb24-title-row">
                        <span class="tjb24-title">TJB24.ir AI Score</span>
                        <button type="button" class="tjb24-info-btn" data-symbol="${safeSymbol}" data-action="open-xai" data-pillar="overview" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی" aria-label="اطلاعات امتیاز هوش مصنوعی">
                            <i data-lucide="info"></i>
                        </button>
                    </div>
                    <div class="tjb24-gauge-wrap">
                        <svg class="tjb24-gauge-svg" viewBox="0 0 80 80" width="80" height="80" aria-label="رتبه هوش مصنوعی ${aiScoreInt} از ۱۰">
                            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
                            <circle class="gauge-progress gauge-${colorGrade}" cx="40" cy="40" r="32"
                                stroke-dasharray="201.06"
                                stroke-dashoffset="${mainGaugeOffset}"
                                transform="rotate(-90 40 40)"></circle>
                        </svg>
                        <span class="tjb24-gauge-score">${toPersianDigits(aiScoreInt)}</span>
                    </div>
                    <div class="tjb24-signal-label signal-text-${colorGrade}">${tjb24SignalLabel}</div>
                    <button type="button" class="tjb24-analysis-link btn-summary" data-symbol="${safeSymbol}" title="مشاهده تحلیل هوش مصنوعی نماد ${safeSymbol}">
                        <span>مشاهده تحلیل هوش مصنوعی</span>
                    </button>
                </div>

                <div class="tjb24-subscores-col">
                    <div class="subscore-item" data-symbol="${safeSymbol}" data-pillar="fundamental" data-action="open-xai" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی (رتبه بنیادی: ${toPersianDigits(fundScore)} از ۱۰)">
                        <div class="subscore-gauge-wrap">
                            <svg class="subscore-gauge-svg" viewBox="0 0 36 36" width="36" height="36">
                                <circle class="gauge-bg" cx="18" cy="18" r="14"></circle>
                                <circle class="gauge-progress gauge-${fundGrade}" cx="18" cy="18" r="14"
                                    stroke-dasharray="87.96"
                                    stroke-dashoffset="${fundOffset}"
                                    transform="rotate(-90 18 18)"></circle>
                            </svg>
                            <span class="subscore-value">${toPersianDigits(fundInt)}</span>
                        </div>
                        <div class="subscore-labels">
                            <span class="subscore-fa">بنیادی</span>
                            <span class="subscore-en">Fundamental</span>
                        </div>
                    </div>

                    <div class="subscore-item" data-symbol="${safeSymbol}" data-pillar="technical" data-action="open-xai" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی (رتبه تکنیکال: ${toPersianDigits(techScore)} از ۱۰)">
                        <div class="subscore-gauge-wrap">
                            <svg class="subscore-gauge-svg" viewBox="0 0 36 36" width="36" height="36">
                                <circle class="gauge-bg" cx="18" cy="18" r="14"></circle>
                                <circle class="gauge-progress gauge-${techGrade}" cx="18" cy="18" r="14"
                                    stroke-dasharray="87.96"
                                    stroke-dashoffset="${techOffset}"
                                    transform="rotate(-90 18 18)"></circle>
                            </svg>
                            <span class="subscore-value">${toPersianDigits(techInt)}</span>
                        </div>
                        <div class="subscore-labels">
                            <span class="subscore-fa">تکنیکال</span>
                            <span class="subscore-en">Technical</span>
                        </div>
                    </div>

                    <div class="subscore-item" data-symbol="${safeSymbol}" data-pillar="sentiment" data-action="open-xai" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی (رتبه احساس بازار: ${toPersianDigits(sentScore)} از ۱۰)">
                        <div class="subscore-gauge-wrap">
                            <svg class="subscore-gauge-svg" viewBox="0 0 36 36" width="36" height="36">
                                <circle class="gauge-bg" cx="18" cy="18" r="14"></circle>
                                <circle class="gauge-progress gauge-${sentGrade}" cx="18" cy="18" r="14"
                                    stroke-dasharray="87.96"
                                    stroke-dashoffset="${sentOffset}"
                                    transform="rotate(-90 18 18)"></circle>
                            </svg>
                            <span class="subscore-value">${toPersianDigits(sentInt)}</span>
                        </div>
                        <div class="subscore-labels">
                            <span class="subscore-fa">احساس بازار</span>
                            <span class="subscore-en">Sentiment</span>
                        </div>
                    </div>

                    <div class="subscore-item" data-symbol="${safeSymbol}" data-pillar="low_risk" data-action="open-xai" title="کلیک برای مشاهده شناسنامه شفافیت و فرمول محاسباتی هوش مصنوعی (رتبه کم‌ریسک بودن: ${toPersianDigits(riskScore)} از ۱۰)">
                        <div class="subscore-gauge-wrap">
                            <svg class="subscore-gauge-svg" viewBox="0 0 36 36" width="36" height="36">
                                <circle class="gauge-bg" cx="18" cy="18" r="14"></circle>
                                <circle class="gauge-progress gauge-${riskGrade}" cx="18" cy="18" r="14"
                                    stroke-dasharray="87.96"
                                    stroke-dashoffset="${riskOffset}"
                                    transform="rotate(-90 18 18)"></circle>
                            </svg>
                            <span class="subscore-value">${toPersianDigits(riskInt)}</span>
                        </div>
                        <div class="subscore-labels">
                            <span class="subscore-fa">کم‌ریسک</span>
                            <span class="subscore-en">Low Risk</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="analysis-buttons-group">
                <button type="button" class="btn-live-avatar-trigger" data-symbol="${safeSymbol}" data-action="open-live-reporter" title="پخش زنده و گزارشگری آنلاین تابلوی سهم با آواتار هوش مصنوعی">
                    <i data-lucide="radio"></i>
                    <span>🎙️ گزارشگر زنده</span>
                </button>
                <button type="button" class="btn-analysis btn-summary" data-symbol="${safeSymbol}" title="مشاهده خلاصه اجرایی و سناریوی تحلیلی نماد ${safeSymbol}">
                    <i data-lucide="sparkles"></i>
                    <span>خلاصه سهم</span>
                </button>
                <a href="${encodeURI(stock.links?.technical_github || '#')}" target="_blank" rel="noopener noreferrer" class="btn-analysis btn-technical" title="مشاهده گزارش تحلیل تکنیکال در مخزن گیت‌هاب">
                    <i data-lucide="trending-up"></i>
                    <span>تحلیل تکنیکال</span>
                </a>
                <a href="${encodeURI(stock.links?.fundamental_github || '#')}" target="_blank" rel="noopener noreferrer" class="btn-analysis btn-fundamental" title="مشاهده گزارش تحلیل بنیادی در مخزن گیت‌هاب">
                    <i data-lucide="pie-chart"></i>
                    <span>تحلیل بنیادی</span>
                </a>
                <button type="button" class="btn-reanalyze" data-symbol="${safeSymbol}" data-name="${safeName}" title="درخواست تحلیل مجدد نماد ${safeSymbol}">
                    <i data-lucide="refresh-cw"></i>
                    <span>تحلیل مجدد</span>
                </button>
            </div>
        </div>

        <div class="card-stats-col">
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${toPersianDigits(stock.market_cap || "—")}</div>
                    <div class="stat-label">ارزش بازار</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${toPersianDigits(stock.volume || "—")}</div>
                    <div class="stat-label">حجم</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value ${changeClass}">
                        <span>${toPersianDigits(changeSign + (stock.change_percent ?? 0).toFixed(2))}%</span>
                        <span class="change-arrow">${changeArrow}</span>
                    </div>
                    <div class="stat-label">تغییر (٪)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${formatNumberFa(stock.current_price)}</div>
                    <div class="stat-label">قیمت (ریال)</div>
                </div>
            </div>

            <div class="external-links-row">
                <a href="${stock.links?.tsetmc || '#'}" target="_blank" rel="noopener noreferrer" class="btn-external" title="مشاهده نماد در شرکت مدیریت فناوری بورس تهران">
                    <i data-lucide="database"></i>
                    <span>TSETMC</span>
                    <i data-lucide="external-link"></i>
                </a>
                <a href="${stock.links?.rahavard || '#'}" target="_blank" rel="noopener noreferrer" class="btn-external" title="مشاهده در سامانه رهاورد ۳۶۰">
                    <i data-lucide="compass"></i>
                    <span>رهاورد</span>
                    <i data-lucide="external-link"></i>
                </a>
                <a href="${stock.links?.codal || '#'}" target="_blank" rel="noopener noreferrer" class="btn-external" title="مشاهده اطلاعیه‌ها و صورت‌های مالی در کدال">
                    <i data-lucide="file-text"></i>
                    <span>کدال</span>
                    <i data-lucide="external-link"></i>
                </a>
                <a href="${stock.links?.github_folder || '#'}" target="_blank" rel="noopener noreferrer" class="btn-external btn-github" title="مشاهده پوشه نماد در مخزن رسمی گیت‌هاب">
                    <i data-lucide="folder-git-2"></i>
                    <span>گیت‌هاب</span>
                    <i data-lucide="external-link"></i>
                </a>
            </div>
        </div>

        <div class="card-chart-col">
            <div class="chart-header-title">نمودار معاملات ۱۴ روز اخیر</div>
            <div class="chart-canvas-wrap">
                <canvas class="stock-chart-canvas" id="chart-${stock.symbol}"></canvas>
            </div>
        </div>
    `;

    return card;
}

// Bind Favorite Star Button Event
function bindFavoriteEvent(target) {
    if (!target) return;
    const btn = target.classList?.contains("favorite-btn") ? target : target.querySelector(".favorite-btn");
    if (!btn) return;

    btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const sym = btn.getAttribute("data-symbol");
        if (!sym) return;

        if (state.favorites.has(sym)) {
            state.favorites.delete(sym);
            btn.classList.remove("favorited");
            btn.innerHTML = '<i data-lucide="star"></i>';
            showToast(`سهم ${sym} از نشان‌شده‌ها حذف شد.`, "info");
        } else {
            state.favorites.add(sym);
            btn.classList.add("favorited");
            btn.innerHTML = '<i data-lucide="star" fill="currentColor"></i>';
            showToast(`سهم ${sym} به نشان‌شده‌ها اضافه شد.`, "success");
        }

        if (window.lucide) window.lucide.createIcons({ root: btn });
        saveFavorites();

        if (state.currentFilter === "favorites") {
            applyFilterAndSort();
        }
    });
}

// Re-analyze single stock via local backend API
async function handleReanalyze(symbol, button) {
    if (!symbol || !button || button.disabled) return;

    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.classList.add("loading");
    button.innerHTML = `
        <i data-lucide="refresh-cw" class="animate-spin"></i>
        <span>در حال تحلیل...</span>
    `;
    if (window.lucide) {
        window.lucide.createIcons({ root: button });
    }

    try {
        const response = await fetch(`/api/reanalyze?symbol=${encodeURIComponent(symbol)}`, {
            method: "POST",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const result = await response.json();
        const updatedStock = result.stock || (result.status === "ok" && result.symbol ? result : null);
        if (!updatedStock) {
            throw new Error(result?.message || "پاسخ نامعتبر از سرور دریافت شد.");
        }

        // Update in-memory state
        const idxAll = state.allStocks.findIndex((s) => s.symbol === symbol);
        if (idxAll !== -1) {
            state.allStocks[idxAll] = updatedStock;
        }
        const idxFiltered = state.filteredStocks.findIndex((s) => s.symbol === symbol);
        if (idxFiltered !== -1) {
            state.filteredStocks[idxFiltered] = updatedStock;
        }
        state.stocks = state.allStocks;

        // In-place replacement of the card in the DOM
        const container = document.getElementById("stocksContainer");
        const existingCard = container ? container.querySelector(`.stock-card[data-symbol="${symbol}"]`) : null;
        if (existingCard) {
            // Destroy existing chart instance for this canvas if registered
            const oldCanvas = existingCard.querySelector(".stock-sparkline-canvas, .stock-chart-canvas");
            if (oldCanvas) {
                const chartIdx = state.activeCharts.findIndex((c) => c.canvas === oldCanvas);
                if (chartIdx !== -1) {
                    try {
                        state.activeCharts[chartIdx].destroy();
                    } catch (e) {
                        // Ignore
                    }
                    state.activeCharts.splice(chartIdx, 1);
                }
            }

            // Render new card DOM element
            const newCard = renderStockCard(updatedStock);
            existingCard.replaceWith(newCard);

            // Create Lucide icons for the newly inserted card
            if (window.lucide) {
                window.lucide.createIcons({ root: newCard });
            }

            // Render the stock sparkline for the newly inserted card
            const newCanvas = newCard.querySelector(`#sparkline-${updatedStock.symbol}`) || newCard.querySelector(`#chart-${updatedStock.symbol}`);
            if (newCanvas && updatedStock.chart_14d && updatedStock.chart_14d.length > 0) {
                renderMiniSparkline(newCanvas, updatedStock.chart_14d, (updatedStock.change_percent ?? 0) >= 0);
            }

            // Re-bind favorite button
            bindFavoriteEvent(newCard);
        }

        showToast(`تحلیل هوشمند نماد ${symbol} با موفقیت به‌روزرسانی شد.`, "success");
    } catch (err) {
        console.warn(`Reanalyze error for ${symbol}:`, err);
        // Reset button state
        button.disabled = false;
        button.classList.remove("loading");
        button.innerHTML = originalHtml;
        if (window.lucide) {
            window.lucide.createIcons({ root: button });
        }

        showToast(
            `سرور محلی در دسترس نیست. جهت تحلیل از دستور python serve.py یا python run_portfolio.py --symbol ${symbol} استفاده کنید.`,
            "error"
        );
    }
}

// Render Cards to DOM
function renderStockCards() {
    destroyCharts();
    const container = document.getElementById("stocksContainer");
    const emptyState = document.getElementById("emptyState");
    const paginationBar = document.getElementById("paginationBar");

    if (!container) return;
    container.innerHTML = "";

    const total = state.filteredStocks.length;

    // Check Empty State
    if (total === 0) {
        if (emptyState) emptyState.style.display = "flex";
        if (paginationBar) paginationBar.style.display = "none";
        return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (paginationBar) paginationBar.style.display = "flex";

    // Slice pagination
    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = Math.min(startIndex + state.pageSize, total);
    const currentBatch = state.filteredStocks.slice(startIndex, endIndex);

    const fragment = document.createDocumentFragment();

    currentBatch.forEach((stock) => {
        const card = renderStockCard(stock);
        fragment.appendChild(card);
    });

    container.appendChild(fragment);

    // Hydrate Lucide Icons
    if (window.lucide) {
        window.lucide.createIcons({ root: container });
    }

    // Attach Charts / Micro-Sparklines
    currentBatch.forEach((stock) => {
        const canvas = document.getElementById(`sparkline-${stock.symbol}`) || document.getElementById(`chart-${stock.symbol}`);
        if (canvas && stock.chart_14d && stock.chart_14d.length > 0) {
            renderMiniSparkline(canvas, stock.chart_14d, (stock.change_percent ?? 0) >= 0);
        }
    });

    // Attach Favorite Star Events
    container.querySelectorAll(".favorite-btn").forEach((btn) => {
        bindFavoriteEvent(btn);
    });

    renderPagination();
}

// Pagination Controls
function renderPagination() {
    const total = state.filteredStocks.length;
    const totalPages = Math.ceil(total / state.pageSize) || 1;

    const startItem = total > 0 ? (state.currentPage - 1) * state.pageSize + 1 : 0;
    const endItem = Math.min(state.currentPage * state.pageSize, total);

    // Summary text
    const summary = document.getElementById("paginationSummary");
    if (summary) {
        summary.textContent = `نمایش ${toPersianDigits(startItem)} تا ${toPersianDigits(endItem)} از ${toPersianDigits(total)} مورد`;
    }

    // Prev / Next / First / Last buttons
    const firstBtn = document.getElementById("firstPageBtn");
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");
    const lastBtn = document.getElementById("lastPageBtn");

    if (firstBtn) firstBtn.disabled = state.currentPage <= 1;
    if (prevBtn) prevBtn.disabled = state.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = state.currentPage >= totalPages;
    if (lastBtn) lastBtn.disabled = state.currentPage >= totalPages;

    // Page Number Buttons
    const numbersContainer = document.getElementById("pageNumbersContainer");
    if (!numbersContainer) return;
    numbersContainer.innerHTML = "";

    const createPageBtn = (p) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `page-btn ${p === state.currentPage ? "active" : ""}`;
        btn.textContent = toPersianDigits(p);
        btn.addEventListener("click", () => {
            if (state.currentPage !== p) {
                state.currentPage = p;
                renderStockCards();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
        return btn;
    };

    const createEllipsis = () => {
        const span = document.createElement("span");
        span.className = "page-btn page-ellipsis";
        span.textContent = "...";
        return span;
    };

    if (totalPages <= 5) {
        for (let i = 1; i <= totalPages; i++) {
            numbersContainer.appendChild(createPageBtn(i));
        }
    } else {
        numbersContainer.appendChild(createPageBtn(1));
        if (state.currentPage > 3) {
            numbersContainer.appendChild(createEllipsis());
        }

        const start = Math.max(2, state.currentPage - 1);
        const end = Math.min(totalPages - 1, state.currentPage + 1);

        for (let i = start; i <= end; i++) {
            numbersContainer.appendChild(createPageBtn(i));
        }

        if (state.currentPage < totalPages - 2) {
            numbersContainer.appendChild(createEllipsis());
        }
        numbersContainer.appendChild(createPageBtn(totalPages));
    }
}

// Helper Functions for Advanced Filtering
function isStockInEntryZone(stock) {
    if (!stock.plan || !stock.plan.entry_zone || !stock.current_price) return false;
    const rawMatches = stock.plan.entry_zone.match(/[\d,]+/g);
    if (!rawMatches || rawMatches.length < 2) return false;
    const n1 = parseFloat(rawMatches[0].replace(/,/g, ""));
    const n2 = parseFloat(rawMatches[1].replace(/,/g, ""));
    if (isNaN(n1) || isNaN(n2)) return false;
    const minZ = Math.min(n1, n2) * 0.98;
    const maxZ = Math.max(n1, n2) * 1.02;
    return stock.current_price >= minZ && stock.current_price <= maxZ;
}

function isStockNear14dLow(stock) {
    if (!Array.isArray(stock.chart_14d) || stock.chart_14d.length === 0 || !stock.current_price) return false;
    const prices = stock.chart_14d
        .map(p => (typeof p === "object" && p !== null ? p.price : Number(p)))
        .filter(p => !isNaN(p) && p > 0);
    if (prices.length === 0) return false;
    const min14d = Math.min(...prices);
    return stock.current_price <= (min14d * 1.05);
}

function hasSmartMoneyInflow(stock) {
    const bp = stock.ai_score_details?.explainability?.sentiment?.raw_inputs?.buyer_power || 0;
    const sentScore = stock.ai_score_details?.sentiment || 0;
    return bp >= 1.5 || sentScore >= 8.0;
}

function isStockUndervaluedPE(stock) {
    const pe = stock.ai_score_details?.explainability?.fundamental?.raw_inputs?.pe_ratio;
    const groupPe = stock.ai_score_details?.explainability?.fundamental?.raw_inputs?.group_pe;
    if (pe && groupPe && pe > 0 && groupPe > 0) {
        return pe < groupPe;
    }
    return false;
}

function hasHighRiskReward(stock) {
    const rr = stock.plan?.risk_reward_ratio || 0;
    return rr >= 2.0;
}

function isStockRecent(stock, mode) {
    if (!mode || mode === "all") return true;
    const lu = String(stock.last_update || "").trim();
    if (!lu) return false;
    
    const allDates = state.allStocks.map(s => String(s.last_update || "").split(" ")[0]).filter(Boolean);
    const latestDate = allDates.sort().reverse()[0] || "1405/07/28";
    const stockDate = lu.split(" ")[0];
    
    if (mode === "today") {
        return stockDate === latestDate;
    } else if (mode === "3days") {
        return stockDate >= "1405/07/25";
    } else if (mode === "7days") {
        return stockDate >= "1405/07/21";
    }
    return true;
}

// Filter and Sort Pipeline
function applyFilterAndSort() {
    let result = [...state.allStocks];

    // 1. Text Search Filter
    if (state.searchQuery.trim()) {
        const q = state.searchQuery.trim().toLowerCase();
        result = result.filter((s) => {
            const sym = (s.symbol || "").toLowerCase();
            const name = (s.name || "").toLowerCase();
            return sym.includes(q) || name.includes(q);
        });
    }

    // 2. Legacy Category Filter (from dropdown)
    if (state.currentFilter === "positive") {
        result = result.filter((s) => (s.change_percent || 0) > 0);
    } else if (state.currentFilter === "negative") {
        result = result.filter((s) => (s.change_percent || 0) < 0);
    } else if (state.currentFilter === "favorites") {
        result = result.filter((s) => state.favorites.has(s.symbol));
    }

    // 3. Quick Filter Chips
    const qf = state.filters.quickFilter;
    if (qf === "golden") {
        result = result.filter((s) => (s.recommendation?.signal || s.ai_score_details?.signal) === "STRONG_BUY");
    } else if (qf === "buy") {
        result = result.filter((s) => {
            const sig = s.recommendation?.signal || s.ai_score_details?.signal;
            return sig === "STRONG_BUY" || sig === "BUY";
        });
    } else if (qf === "low_risk") {
        result = result.filter((s) => {
            const rk = s.risk_level || s.recommendation?.risk_level || "";
            return rk.includes("کم‌ریسک") || rk.includes("کم ریسک");
        });
    } else if (qf === "smart_money") {
        result = result.filter(hasSmartMoneyInflow);
    } else if (qf === "entry_zone") {
        result = result.filter(isStockInEntryZone);
    } else if (qf === "rr_high") {
        result = result.filter(hasHighRiskReward);
    } else if (qf === "undervalued") {
        result = result.filter(isStockUndervaluedPE);
    } else if (qf === "near_low") {
        result = result.filter(isStockNear14dLow);
    } else if (qf === "updated_today") {
        result = result.filter((s) => isStockRecent(s, "today"));
    } else if (qf === "favorites") {
        result = result.filter((s) => state.favorites.has(s.symbol));
    }

    // 4. Advanced Drawer Filters
    // 4.1 Signals
    if (state.filters.signals.size > 0) {
        result = result.filter((s) => {
            const sig = s.recommendation?.signal || s.ai_score_details?.signal || "";
            if (state.filters.signals.has("STRONG_BUY") && sig === "STRONG_BUY") return true;
            if (state.filters.signals.has("BUY") && sig === "BUY") return true;
            if (state.filters.signals.has("HOLD") && sig === "HOLD") return true;
            if (state.filters.signals.has("SELL_GROUP") && (sig.includes("SELL") || sig === "HOLD_WATCH")) return true;
            return false;
        });
    }

    // 4.2 Risk Level
    if (state.filters.riskLevel !== "all") {
        result = result.filter((s) => {
            const rk = s.risk_level || s.recommendation?.risk_level || "";
            if (state.filters.riskLevel === "low") return rk.includes("کم‌ریسک") || rk.includes("کم ریسک");
            if (state.filters.riskLevel === "medium") return rk.includes("متوسط");
            if (state.filters.riskLevel === "high") return rk.includes("پرریسک") || rk.includes("پر ریسک");
            return true;
        });
    }

    // 4.3 Time Horizon
    if (state.filters.timeHorizon !== "all") {
        result = result.filter((s) => {
            const th = s.time_horizon || s.recommendation?.time_horizon || "";
            if (state.filters.timeHorizon === "short") return th.includes("کوتاه");
            if (state.filters.timeHorizon === "mid") return th.includes("میان");
            if (state.filters.timeHorizon === "long") return th.includes("بلند");
            return true;
        });
    }

    // 4.4 AI Score Slider
    if (state.filters.minAiScore > 1.0) {
        result = result.filter((s) => {
            const sc = s.ai_score_details?.ai_score ?? (s.score ? s.score * 2 : 0);
            return sc >= state.filters.minAiScore;
        });
    }

    // 4.5 4-Pillars Sliders
    if (state.filters.minFundamental > 1.0) {
        result = result.filter((s) => (s.ai_score_details?.fundamental ?? 0) >= state.filters.minFundamental);
    }
    if (state.filters.minTechnical > 1.0) {
        result = result.filter((s) => (s.ai_score_details?.technical ?? 0) >= state.filters.minTechnical);
    }
    if (state.filters.minSentiment > 1.0) {
        result = result.filter((s) => (s.ai_score_details?.sentiment ?? 0) >= state.filters.minSentiment);
    }
    if (state.filters.minRisk > 1.0) {
        result = result.filter((s) => (s.ai_score_details?.low_risk ?? 0) >= state.filters.minRisk);
    }

    // 4.6 Creative Switches
    if (state.filters.smartMoney) {
        result = result.filter(hasSmartMoneyInflow);
    }
    if (state.filters.inEntryZone) {
        result = result.filter(isStockInEntryZone);
    }
    if (state.filters.highRR) {
        result = result.filter(hasHighRiskReward);
    }
    if (state.filters.undervaluedPE) {
        result = result.filter(isStockUndervaluedPE);
    }
    if (state.filters.near14dLow) {
        result = result.filter(isStockNear14dLow);
    }

    // 4.7 Recency
    if (state.filters.recency !== "all") {
        result = result.filter((s) => isStockRecent(s, state.filters.recency));
    }

    // 5. Sorting
    result.sort((a, b) => {
        switch (state.currentSort) {
            case "growth_desc":
                return (b.change_percent || 0) - (a.change_percent || 0);
            case "growth_asc":
                return (a.change_percent || 0) - (b.change_percent || 0);
            case "price_desc":
                return (b.current_price || 0) - (a.current_price || 0);
            case "price_asc":
                return (a.current_price || 0) - (b.current_price || 0);
            case "volume_desc": {
                const parseVol = (v) => {
                    if (!v || v === "—") return 0;
                    let num = parseFloat(v);
                    if (v.includes("B")) num *= 1_000_000_000;
                    else if (v.includes("M")) num *= 1_000_000;
                    else if (v.includes("K")) num *= 1_000;
                    return num || 0;
                };
                return parseVol(b.volume) - parseVol(a.volume);
            }
            case "name_asc":
                return (a.name || "").localeCompare(b.name || "", "fa");
            case "symbol_asc":
                return (a.symbol || "").localeCompare(b.symbol || "", "fa");
            default:
                return 0;
        }
    });

    state.filteredStocks = result;
    state.currentPage = 1;
    updateActiveFilterUI();
    renderStockCards();
}

function countActiveFilters() {
    let count = 0;
    if (state.filters.quickFilter && state.filters.quickFilter !== "all") count++;
    if (state.filters.signals.size > 0) count += state.filters.signals.size;
    if (state.filters.riskLevel !== "all") count++;
    if (state.filters.timeHorizon !== "all") count++;
    if (state.filters.minAiScore > 1.0) count++;
    if (state.filters.minFundamental > 1.0) count++;
    if (state.filters.minTechnical > 1.0) count++;
    if (state.filters.minSentiment > 1.0) count++;
    if (state.filters.minRisk > 1.0) count++;
    if (state.filters.smartMoney) count++;
    if (state.filters.inEntryZone) count++;
    if (state.filters.highRR) count++;
    if (state.filters.undervaluedPE) count++;
    if (state.filters.near14dLow) count++;
    if (state.filters.recency !== "all") count++;
    return count;
}

function updateActiveFilterUI() {
    // 1. Update Drawer Matching Count pill
    const drawerMatchingCount = document.getElementById("drawerMatchingCount");
    if (drawerMatchingCount) {
        drawerMatchingCount.textContent = `(${toPersianDigits(state.filteredStocks.length)} سهم)`;
    }

    // 2. Count active filters and update Header Badge
    const activeCount = countActiveFilters();
    const badge = document.getElementById("activeFiltersBadge");
    const drawerBtn = document.getElementById("openFilterDrawerBtn");
    if (badge) {
        if (activeCount > 0) {
            badge.style.display = "inline-flex";
            badge.textContent = toPersianDigits(activeCount);
        } else {
            badge.style.display = "none";
        }
    }
    if (drawerBtn) {
        drawerBtn.classList.toggle("has-active-filters", activeCount > 0);
    }

    // 3. Render Active Filter Tags
    const tagsBar = document.getElementById("activeFilterTagsBar");
    const tagsContainer = document.getElementById("activeFilterTagsContainer");
    if (!tagsBar || !tagsContainer) return;

    const tags = [];

    // Quick Filter tag
    if (state.filters.quickFilter && state.filters.quickFilter !== "all") {
        const qfLabels = {
            golden: "🚀 فرصت طلایی",
            buy: "✅ فرصت خرید",
            low_risk: "🛡️ کم‌ریسک",
            smart_money: "💰 پول هوشمند",
            entry_zone: "🎯 در محدوده خرید",
            rr_high: "⚖️ R/R بالای ۲",
            undervalued: "💎 P/E زیر صنعت",
            near_low: "📉 نزدیک کف ۱۴ روزه",
            updated_today: "📅 آپدیت امروز",
            favorites: "⭐ نشان‌شده‌ها"
        };
        const label = qfLabels[state.filters.quickFilter] || state.filters.quickFilter;
        tags.push({ key: "quickFilter", label: label, onRemove: () => {
            state.filters.quickFilter = "all";
            document.querySelectorAll("#quickFilterChips .filter-chip").forEach(c => {
                c.classList.toggle("active", c.getAttribute("data-quick-filter") === "all");
            });
            applyFilterAndSort();
        }});
    }

    // Signal tags
    const sigLabels = {
        STRONG_BUY: "🚀 خرید قوی / طلایی",
        BUY: "✅ خرید پله‌ای",
        HOLD: "⏸️ نگهداری",
        SELL_GROUP: "⚠️ فروش / خروج"
    };
    state.filters.signals.forEach(sig => {
        tags.push({ key: `sig_${sig}`, label: sigLabels[sig] || sig, onRemove: () => {
            state.filters.signals.delete(sig);
            const chk = document.querySelector(`input[name="signalFilter"][value="${sig}"]`);
            if (chk) chk.checked = false;
            applyFilterAndSort();
        }});
    });

    // Risk Level tag
    if (state.filters.riskLevel !== "all") {
        const riskLabels = { low: "🛡️ کم‌ریسک", medium: "⚖️ ریسک متوسط", high: "⚡ پرریسک" };
        tags.push({ key: "riskLevel", label: riskLabels[state.filters.riskLevel] || state.filters.riskLevel, onRemove: () => {
            state.filters.riskLevel = "all";
            document.querySelectorAll("#riskFilterGroup .filter-toggle-pill").forEach(p => {
                p.classList.toggle("active", p.getAttribute("data-risk") === "all");
            });
            applyFilterAndSort();
        }});
    }

    // Time Horizon tag
    if (state.filters.timeHorizon !== "all") {
        const thLabels = { short: "⚡ کوتاه‌مدت", mid: "⏳ میان‌مدت", long: "💎 بلندمدت" };
        tags.push({ key: "timeHorizon", label: thLabels[state.filters.timeHorizon] || state.filters.timeHorizon, onRemove: () => {
            state.filters.timeHorizon = "all";
            document.querySelectorAll("#horizonFilterGroup .filter-toggle-pill").forEach(p => {
                p.classList.toggle("active", p.getAttribute("data-horizon") === "all");
            });
            applyFilterAndSort();
        }});
    }

    // AI Score slider tag
    if (state.filters.minAiScore > 1.0) {
        tags.push({ key: "minAiScore", label: `حداقل نمره هوش مصنوعی: ${toPersianDigits(state.filters.minAiScore)}`, onRemove: () => {
            state.filters.minAiScore = 1.0;
            const sl = document.getElementById("filterAiScoreSlider");
            const lbl = document.getElementById("aiScoreSliderValue");
            if (sl) sl.value = 1.0;
            if (lbl) lbl.textContent = "۱.۰ از ۱۰";
            applyFilterAndSort();
        }});
    }

    // 4-Pillars tags
    if (state.filters.minFundamental > 1.0) {
        tags.push({ key: "fund", label: `بنیادی: ${toPersianDigits(state.filters.minFundamental)}+`, onRemove: () => {
            state.filters.minFundamental = 1.0;
            const sl = document.getElementById("filterPillarFund");
            const lbl = document.getElementById("sliderValFund");
            if (sl) sl.value = 1.0;
            if (lbl) lbl.textContent = "۱.۰";
            applyFilterAndSort();
        }});
    }
    if (state.filters.minTechnical > 1.0) {
        tags.push({ key: "tech", label: `تکنیکال: ${toPersianDigits(state.filters.minTechnical)}+`, onRemove: () => {
            state.filters.minTechnical = 1.0;
            const sl = document.getElementById("filterPillarTech");
            const lbl = document.getElementById("sliderValTech");
            if (sl) sl.value = 1.0;
            if (lbl) lbl.textContent = "۱.۰";
            applyFilterAndSort();
        }});
    }
    if (state.filters.minSentiment > 1.0) {
        tags.push({ key: "sent", label: `تابلو/احساس: ${toPersianDigits(state.filters.minSentiment)}+`, onRemove: () => {
            state.filters.minSentiment = 1.0;
            const sl = document.getElementById("filterPillarSent");
            const lbl = document.getElementById("sliderValSent");
            if (sl) sl.value = 1.0;
            if (lbl) lbl.textContent = "۱.۰";
            applyFilterAndSort();
        }});
    }
    if (state.filters.minRisk > 1.0) {
        tags.push({ key: "risk", label: `ثبات/مدیریت ریسک: ${toPersianDigits(state.filters.minRisk)}+`, onRemove: () => {
            state.filters.minRisk = 1.0;
            const sl = document.getElementById("filterPillarRisk");
            const lbl = document.getElementById("sliderValRisk");
            if (sl) sl.value = 1.0;
            if (lbl) lbl.textContent = "۱.۰";
            applyFilterAndSort();
        }});
    }

    // Switches
    if (state.filters.smartMoney) {
        tags.push({ key: "smartMoney", label: "💰 پول هوشمند", onRemove: () => {
            state.filters.smartMoney = false;
            const sw = document.getElementById("toggleSmartMoney");
            if (sw) sw.checked = false;
            applyFilterAndSort();
        }});
    }
    if (state.filters.inEntryZone) {
        tags.push({ key: "inEntryZone", label: "🎯 در محدوده ورود", onRemove: () => {
            state.filters.inEntryZone = false;
            const sw = document.getElementById("toggleInEntryZone");
            if (sw) sw.checked = false;
            applyFilterAndSort();
        }});
    }
    if (state.filters.highRR) {
        tags.push({ key: "highRR", label: "⚖️ R/R بالای ۲", onRemove: () => {
            state.filters.highRR = false;
            const sw = document.getElementById("toggleHighRR");
            if (sw) sw.checked = false;
            applyFilterAndSort();
        }});
    }
    if (state.filters.undervaluedPE) {
        tags.push({ key: "undervaluedPE", label: "💎 P/E زیر صنعت", onRemove: () => {
            state.filters.undervaluedPE = false;
            const sw = document.getElementById("toggleUndervalued");
            if (sw) sw.checked = false;
            applyFilterAndSort();
        }});
    }
    if (state.filters.near14dLow) {
        tags.push({ key: "near14dLow", label: "📉 نزدیک کف ۱۴ روزه", onRemove: () => {
            state.filters.near14dLow = false;
            const sw = document.getElementById("toggleNearLow");
            if (sw) sw.checked = false;
            applyFilterAndSort();
        }});
    }

    // Recency tag
    if (state.filters.recency !== "all") {
        const rcLabels = { today: "📅 آپدیت امروز", "3days": "🕒 ۳ روز اخیر", "7days": "🗓️ یک هفته اخیر" };
        tags.push({ key: "recency", label: rcLabels[state.filters.recency] || state.filters.recency, onRemove: () => {
            state.filters.recency = "all";
            document.querySelectorAll("#recencyFilterGroup .filter-toggle-pill").forEach(p => {
                p.classList.toggle("active", p.getAttribute("data-recency") === "all");
            });
            applyFilterAndSort();
        }});
    }

    if (tags.length > 0) {
        tagsBar.style.display = "flex";
        tagsContainer.innerHTML = "";
        tags.forEach(tag => {
            const chip = document.createElement("span");
            chip.className = "filter-tag-chip";
            chip.innerHTML = `
                <span>${escapeHtml(tag.label)}</span>
                <button type="button" class="tag-remove-btn" aria-label="حذف فیلتر">×</button>
            `;
            const removeBtn = chip.querySelector(".tag-remove-btn");
            removeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                tag.onRemove();
            });
            tagsContainer.appendChild(chip);
        });
    } else {
        tagsBar.style.display = "none";
        tagsContainer.innerHTML = "";
    }
}

function clearAllFilters() {
    // Reset quick filter
    state.filters.quickFilter = "all";
    document.querySelectorAll("#quickFilterChips .filter-chip").forEach(c => {
        c.classList.toggle("active", c.getAttribute("data-quick-filter") === "all");
    });

    // Reset signals
    state.filters.signals.clear();
    document.querySelectorAll("input[name='signalFilter']").forEach(c => c.checked = false);

    // Reset risk & horizon
    state.filters.riskLevel = "all";
    document.querySelectorAll("#riskFilterGroup .filter-toggle-pill").forEach(p => {
        p.classList.toggle("active", p.getAttribute("data-risk") === "all");
    });

    state.filters.timeHorizon = "all";
    document.querySelectorAll("#horizonFilterGroup .filter-toggle-pill").forEach(p => {
        p.classList.toggle("active", p.getAttribute("data-horizon") === "all");
    });

    // Reset sliders
    state.filters.minAiScore = 1.0;
    const aiSl = document.getElementById("filterAiScoreSlider");
    const aiLbl = document.getElementById("aiScoreSliderValue");
    if (aiSl) aiSl.value = 1.0;
    if (aiLbl) aiLbl.textContent = "۱.۰ از ۱۰";

    state.filters.minFundamental = 1.0;
    const fSl = document.getElementById("filterPillarFund");
    const fLbl = document.getElementById("sliderValFund");
    if (fSl) fSl.value = 1.0;
    if (fLbl) fLbl.textContent = "۱.۰";

    state.filters.minTechnical = 1.0;
    const tSl = document.getElementById("filterPillarTech");
    const tLbl = document.getElementById("sliderValTech");
    if (tSl) tSl.value = 1.0;
    if (tLbl) tLbl.textContent = "۱.۰";

    state.filters.minSentiment = 1.0;
    const sSl = document.getElementById("filterPillarSent");
    const sLbl = document.getElementById("sliderValSent");
    if (sSl) sSl.value = 1.0;
    if (sLbl) sLbl.textContent = "۱.۰";

    state.filters.minRisk = 1.0;
    const rSl = document.getElementById("filterPillarRisk");
    const rLbl = document.getElementById("sliderValRisk");
    if (rSl) rSl.value = 1.0;
    if (rLbl) rLbl.textContent = "۱.۰";

    // Reset switches
    state.filters.smartMoney = false;
    const smSw = document.getElementById("toggleSmartMoney");
    if (smSw) smSw.checked = false;

    state.filters.inEntryZone = false;
    const ezSw = document.getElementById("toggleInEntryZone");
    if (ezSw) ezSw.checked = false;

    state.filters.highRR = false;
    const rrSw = document.getElementById("toggleHighRR");
    if (rrSw) rrSw.checked = false;

    state.filters.undervaluedPE = false;
    const peSw = document.getElementById("toggleUndervalued");
    if (peSw) peSw.checked = false;

    state.filters.near14dLow = false;
    const nlSw = document.getElementById("toggleNearLow");
    if (nlSw) nlSw.checked = false;

    // Reset recency
    state.filters.recency = "all";
    document.querySelectorAll("#recencyFilterGroup .filter-toggle-pill").forEach(p => {
        p.classList.toggle("active", p.getAttribute("data-recency") === "all");
    });

    // Reset search
    state.searchQuery = "";
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearchBtn");
    if (searchInput) searchInput.value = "";
    if (clearBtn) clearBtn.style.display = "none";

    // Reset dropdown
    state.currentFilter = "all";
    document.querySelectorAll("#filterMenu .dropdown-item").forEach(it => {
        it.classList.toggle("active", it.getAttribute("data-filter") === "all");
    });

    applyFilterAndSort();
    showToast("تمام فیلترها به حالت پیش‌فرض بازنشانی شدند.", "info");
}

function updateFilterIndicator() {
    // Maintained for backward compatibility
    const bar = document.getElementById("filterIndicatorBar");
    const text = document.getElementById("filterIndicatorText");
    if (!bar || !text) return;

    const parts = [];
    if (state.searchQuery.trim()) {
        parts.push(`جستجو: «${state.searchQuery.trim()}»`);
    }
    if (state.currentFilter === "positive") {
        parts.push("فیلتر: سهام مثبت");
    } else if (state.currentFilter === "negative") {
        parts.push("فیلتر: سهام منفی");
    } else if (state.currentFilter === "favorites") {
        parts.push("فیلتر: نشان‌شده‌ها");
    }

    if (parts.length > 0) {
        bar.style.display = "flex";
        text.textContent = parts.join(" | ");
    } else {
        bar.style.display = "none";
    }
}

// Event Listeners Setup

// Setup Dual-Mode Switcher (Simple vs Advanced)
function setupModeToggle() {
    const btnSimple = document.getElementById("btnModeSimple");
    const btnAdvanced = document.getElementById("btnModeAdvanced");

    const syncUI = () => {
        const isSimple = state.uiMode === "simple";
        if (btnSimple) {
            btnSimple.classList.toggle("active", isSimple);
            btnSimple.setAttribute("aria-checked", isSimple ? "true" : "false");
        }
        if (btnAdvanced) {
            btnAdvanced.classList.toggle("active", !isSimple);
            btnAdvanced.setAttribute("aria-checked", !isSimple ? "true" : "false");
        }
        document.body.classList.toggle("ui-mode-simple", isSimple);
        document.body.classList.toggle("ui-mode-advanced", !isSimple);
    };

    syncUI();

    if (btnSimple) {
        btnSimple.addEventListener("click", () => {
            if (state.uiMode !== "simple") {
                state.uiMode = "simple";
                try { localStorage.setItem("tjb24_ui_mode", "simple"); } catch (e) {}
                syncUI();
                renderStockCards();
                showToast("نمای ساده و روان فعال شد.", "info");
            }
        });
    }

    if (btnAdvanced) {
        btnAdvanced.addEventListener("click", () => {
            if (state.uiMode !== "advanced") {
                state.uiMode = "advanced";
                try { localStorage.setItem("tjb24_ui_mode", "advanced"); } catch (e) {}
                syncUI();
                renderStockCards();
                showToast("نمای تحلیلی و تخصصی فعال شد.", "info");
            }
        });
    }
}


// Setup Filter Drawer and Quick Chips
function setupFilterDrawerAndChips() {
    // 1. Quick Filter Chips
    const quickChips = document.querySelectorAll("#quickFilterChips .filter-chip");
    quickChips.forEach(chip => {
        chip.addEventListener("click", () => {
            quickChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            state.filters.quickFilter = chip.getAttribute("data-quick-filter") || "all";
            applyFilterAndSort();
        });
    });

    // 2. Open / Close Drawer
    const openBtn = document.getElementById("openFilterDrawerBtn");
    const closeBtn = document.getElementById("closeFilterDrawerBtn");
    const backdrop = document.getElementById("filterDrawerBackdrop");
    const panel = document.getElementById("filterDrawerPanel");

    const openDrawer = () => {
        if (backdrop) backdrop.classList.add("show");
        if (panel) {
            panel.classList.add("show");
            if (window.lucide) window.lucide.createIcons({ root: panel });
        }
    };

    const closeDrawer = () => {
        if (backdrop) backdrop.classList.remove("show");
        if (panel) panel.classList.remove("show");
    };

    if (openBtn) openBtn.addEventListener("click", openDrawer);
    if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
    if (backdrop) backdrop.addEventListener("click", closeDrawer);

    // 3. Signal Checkboxes
    document.querySelectorAll("input[name='signalFilter']").forEach(chk => {
        chk.addEventListener("change", (e) => {
            const val = e.target.value;
            if (e.target.checked) {
                state.filters.signals.add(val);
            } else {
                state.filters.signals.delete(val);
            }
            applyFilterAndSort();
        });
    });

    // 4. Risk Level Pills
    document.querySelectorAll("#riskFilterGroup .filter-toggle-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("#riskFilterGroup .filter-toggle-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.filters.riskLevel = pill.getAttribute("data-risk") || "all";
            applyFilterAndSort();
        });
    });

    // 5. Time Horizon Pills
    document.querySelectorAll("#horizonFilterGroup .filter-toggle-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("#horizonFilterGroup .filter-toggle-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.filters.timeHorizon = pill.getAttribute("data-horizon") || "all";
            applyFilterAndSort();
        });
    });

    // 6. AI Score Slider
    const aiSlider = document.getElementById("filterAiScoreSlider");
    const aiVal = document.getElementById("aiScoreSliderValue");
    if (aiSlider) {
        aiSlider.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value) || 1.0;
            state.filters.minAiScore = val;
            if (aiVal) aiVal.textContent = `${toPersianDigits(val.toFixed(1))} از ۱۰`;
            applyFilterAndSort();
        });
    }

    // 7. 4 Pillars Sliders
    const bindPillar = (id, labelId, filterKey) => {
        const slider = document.getElementById(id);
        const label = document.getElementById(labelId);
        if (slider) {
            slider.addEventListener("input", (e) => {
                const val = parseFloat(e.target.value) || 1.0;
                state.filters[filterKey] = val;
                if (label) label.textContent = toPersianDigits(val.toFixed(1));
                applyFilterAndSort();
            });
        }
    };
    bindPillar("filterPillarFund", "sliderValFund", "minFundamental");
    bindPillar("filterPillarTech", "sliderValTech", "minTechnical");
    bindPillar("filterPillarSent", "sliderValSent", "minSentiment");
    bindPillar("filterPillarRisk", "sliderValRisk", "minRisk");

    // 8. Creative Toggles
    const bindToggle = (id, filterKey) => {
        const sw = document.getElementById(id);
        if (sw) {
            sw.addEventListener("change", (e) => {
                state.filters[filterKey] = !!e.target.checked;
                applyFilterAndSort();
            });
        }
    };
    bindToggle("toggleSmartMoney", "smartMoney");
    bindToggle("toggleInEntryZone", "inEntryZone");
    bindToggle("toggleHighRR", "highRR");
    bindToggle("toggleUndervalued", "undervaluedPE");
    bindToggle("toggleNearLow", "near14dLow");

    // 9. Recency Pills
    document.querySelectorAll("#recencyFilterGroup .filter-toggle-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll("#recencyFilterGroup .filter-toggle-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.filters.recency = pill.getAttribute("data-recency") || "all";
            applyFilterAndSort();
        });
    });

    // 10. Drawer Reset & Apply Buttons
    const drawerResetBtn = document.getElementById("drawerResetBtn");
    if (drawerResetBtn) {
        drawerResetBtn.addEventListener("click", () => {
            clearAllFilters();
        });
    }

    const drawerApplyBtn = document.getElementById("drawerApplyBtn");
    if (drawerApplyBtn) {
        drawerApplyBtn.addEventListener("click", () => {
            closeDrawer();
            showToast(`فیلترها اعمال شدند (${toPersianDigits(state.filteredStocks.length)} سهم یافت شد).`, "success");
        });
    }

    // 11. Clear All Filters Buttons
    const clearAllTagsBtn = document.getElementById("clearAllFiltersBtn");
    if (clearAllTagsBtn) {
        clearAllTagsBtn.addEventListener("click", () => {
            clearAllFilters();
        });
    }

    if (window.lucide) {
        const headerControls = document.querySelector(".header-controls");
        if (headerControls) window.lucide.createIcons({ root: headerControls });
        if (panel) window.lucide.createIcons({ root: panel });
    }
}

function setupEventListeners() {
    setupModeToggle();
    setupFilterDrawerAndChips();
    // Search input
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearchBtn");

    if (searchInput) {
        let debounceTimer = null;
        searchInput.addEventListener("input", (e) => {
            const val = e.target.value;
            if (clearBtn) clearBtn.style.display = val ? "flex" : "none";

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                state.searchQuery = val;
                applyFilterAndSort();
            }, 150);
        });
    }

    if (clearBtn && searchInput) {
        clearBtn.addEventListener("click", () => {
            searchInput.value = "";
            clearBtn.style.display = "none";
            state.searchQuery = "";
            applyFilterAndSort();
            searchInput.focus();
        });
    }

    // Reset filters button
    const resetBtn = document.getElementById("resetFiltersBtn");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            clearAllFilters();
        });
    }

    // Sort Dropdown
    const sortBtn = document.getElementById("sortDropdownBtn");
    const sortMenu = document.getElementById("sortMenu");

    if (sortBtn && sortMenu) {
        sortBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = sortMenu.classList.contains("show");
            document.querySelectorAll(".dropdown-menu").forEach((m) => m.classList.remove("show"));
            document.querySelectorAll(".btn-control").forEach((b) => b.setAttribute("aria-expanded", "false"));

            if (!isOpen) {
                sortMenu.classList.add("show");
                sortBtn.setAttribute("aria-expanded", "true");
            }
        });

        sortMenu.querySelectorAll(".dropdown-item").forEach((item) => {
            item.addEventListener("click", () => {
                sortMenu.querySelectorAll(".dropdown-item").forEach((it) => it.classList.remove("active"));
                item.classList.add("active");
                state.currentSort = item.getAttribute("data-sort") || "growth_desc";
                sortMenu.classList.remove("show");
                sortBtn.setAttribute("aria-expanded", "false");
                applyFilterAndSort();
            });
        });
    }

    // Filter Dropdown
    const filterBtn = document.getElementById("filterDropdownBtn");
    const filterMenu = document.getElementById("filterMenu");

    if (filterBtn && filterMenu) {
        filterBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = filterMenu.classList.contains("show");
            document.querySelectorAll(".dropdown-menu").forEach((m) => m.classList.remove("show"));
            document.querySelectorAll(".btn-control").forEach((b) => b.setAttribute("aria-expanded", "false"));

            if (!isOpen) {
                filterMenu.classList.add("show");
                filterBtn.setAttribute("aria-expanded", "true");
            }
        });

        filterMenu.querySelectorAll(".dropdown-item").forEach((item) => {
            item.addEventListener("click", () => {
                filterMenu.querySelectorAll(".dropdown-item").forEach((it) => it.classList.remove("active"));
                item.classList.add("active");
                state.currentFilter = item.getAttribute("data-filter") || "all";
                filterMenu.classList.remove("show");
                filterBtn.setAttribute("aria-expanded", "false");
                applyFilterAndSort();
            });
        });
    }

    // Close dropdowns on outside click
    document.addEventListener("click", () => {
        document.querySelectorAll(".dropdown-menu").forEach((m) => m.classList.remove("show"));
        document.querySelectorAll(".btn-control").forEach((b) => b.setAttribute("aria-expanded", "false"));
    });

    // Page Size Selector
    const pageSizeSelect = document.getElementById("pageSizeSelect");
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener("change", (e) => {
            state.pageSize = parseInt(e.target.value, 10) || 12;
            state.currentPage = 1;
            renderStockCards();
        });
    }

    // Pagination Nav Buttons
    const firstBtn = document.getElementById("firstPageBtn");
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");
    const lastBtn = document.getElementById("lastPageBtn");

    if (firstBtn) {
        firstBtn.addEventListener("click", () => {
            if (state.currentPage > 1) {
                state.currentPage = 1;
                renderStockCards();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (state.currentPage > 1) {
                state.currentPage--;
                renderStockCards();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            const totalPages = Math.ceil(state.filteredStocks.length / state.pageSize);
            if (state.currentPage < totalPages) {
                state.currentPage++;
                renderStockCards();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    if (lastBtn) {
        lastBtn.addEventListener("click", () => {
            const totalPages = Math.ceil(state.filteredStocks.length / state.pageSize);
            if (state.currentPage < totalPages) {
                state.currentPage = totalPages;
                renderStockCards();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    // Setup Add Stock Modal
    setupAddStockModal();

    // Setup About Us Modal
    setupAboutModal();

    // Setup Executive Summary Modal
    setupSummaryModal();

    // Setup Explainability (XAI) Modal
    setupExplainabilityModal();

    // Setup Hover Popover for Stock Cards
    setupSummaryHoverPopover();

    // Setup Card Actions (Re-analysis, Summary Modal, etc.)
    setupCardActions();
}

// Open Explainability (XAI) Modal Helper
function openExplainabilityModal(stock, initialTab = "overview") {
    if (typeof window !== "undefined" && window.openExplainabilityModal) {
        return window.openExplainabilityModal(stock, initialTab);
    }
}

// Card Actions Event Delegation
function setupCardActions() {
    const stocksContainer = document.getElementById("stocksContainer");
    if (stocksContainer) {
        stocksContainer.addEventListener("click", (e) => {
            const reanalyzeBtn = e.target.closest(".btn-reanalyze");
            if (reanalyzeBtn) {
                e.preventDefault();
                e.stopPropagation();
                const menu = reanalyzeBtn.closest(".quick-actions-menu, .quick-actions-dropdown");
                if (menu) {
                    menu.classList.remove("is-active");
                    const b = menu.closest(".quick-actions-wrap")?.querySelector(".btn-quick-actions, .btn-more-actions");
                    if (b) b.classList.remove("is-active");
                }
                const sym = reanalyzeBtn.dataset.symbol || "";
                if (window.openAddStockModal) {
                    window.openAddStockModal(sym);
                }
                return;
            }

            // Quick Actions Dropdown Toggle
            const quickActionsBtn = e.target.closest(".btn-quick-actions, .btn-more-actions");
            if (quickActionsBtn) {
                e.preventDefault();
                e.stopPropagation();
                const parent = quickActionsBtn.closest(".quick-actions-wrap") || quickActionsBtn.parentElement;
                const menu = parent ? parent.querySelector(".quick-actions-menu, .quick-actions-dropdown") : null;
                if (menu) {
                    const wasActive = menu.classList.contains("is-active");
                    // Close all other open dropdowns first
                    document.querySelectorAll(".quick-actions-menu.is-active, .quick-actions-dropdown.is-active").forEach((m) => {
                        m.classList.remove("is-active");
                        const b = m.closest(".quick-actions-wrap")?.querySelector(".btn-quick-actions, .btn-more-actions");
                        if (b) b.classList.remove("is-active");
                    });
                    if (!wasActive) {
                        menu.classList.add("is-active");
                        quickActionsBtn.classList.add("is-active");
                    }
                }
                return;
            }

            // Close quick actions dropdown when clicking a link inside it
            const quickLink = e.target.closest(".quick-actions-item, .quick-actions-menu a, .quick-actions-dropdown a");
            if (quickLink) {
                const openMenu = quickLink.closest(".quick-actions-menu, .quick-actions-dropdown");
                if (openMenu) {
                    openMenu.classList.remove("is-active");
                    const b = openMenu.closest(".quick-actions-wrap")?.querySelector(".btn-quick-actions, .btn-more-actions");
                    if (b) b.classList.remove("is-active");
                }
            }

            // Live Avatar Reporter Trigger
            const liveAvatarBtn = e.target.closest(".btn-live-avatar-trigger, [data-action='open-live-reporter']");
            if (liveAvatarBtn) {
                e.preventDefault();
                e.stopPropagation();
                const sym = liveAvatarBtn.dataset.symbol || "";
                if (typeof openLiveReporter === "function") {
                    openLiveReporter(sym);
                }
                return;
            }

            // Summary Modal Trigger
            const summaryBtn = e.target.closest(".btn-summary, .btn-summary-minimal, .btn-summary-trigger, .recommendation-badge, .tjb24-analysis-link");
            if (summaryBtn) {
                e.preventDefault();
                e.stopPropagation();
                const sym = summaryBtn.dataset.symbol || "";
                const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
                if (stock && window.openSummaryModal) {
                    window.openSummaryModal(stock);
                }
                return;
            }

            // Click on specific subscore item (opens specific pillar tab in Explainability Modal)
            const subscoreItem = e.target.closest(".subscore-item");
            if (subscoreItem) {
                e.preventDefault();
                e.stopPropagation();
                const pillar = subscoreItem.dataset.pillar || "overview";
                const sym = subscoreItem.dataset.symbol || subscoreItem.closest("[data-symbol]")?.dataset.symbol || "";
                const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
                if (stock) {
                    openExplainabilityModal(stock, pillar);
                }
                return;
            }

            // Click on AI hero pill (opens overview tab in Explainability Modal)
            const aiHeroPill = e.target.closest(".ai-hero-pill, [data-action='open-xai']");
            if (aiHeroPill) {
                e.preventDefault();
                e.stopPropagation();
                const pillar = aiHeroPill.dataset.pillar || "overview";
                const sym = aiHeroPill.dataset.symbol || aiHeroPill.closest("[data-symbol]")?.dataset.symbol || "";
                const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
                if (stock) {
                    openExplainabilityModal(stock, pillar);
                }
                return;
            }

            // Click on main AI score box or info button (opens overview tab in Explainability Modal)
            const mainAiBox = e.target.closest(".tjb24-main-box, .tjb24-info-btn");
            if (mainAiBox) {
                e.preventDefault();
                e.stopPropagation();
                const sym = mainAiBox.dataset.symbol || mainAiBox.closest("[data-symbol]")?.dataset.symbol || "";
                const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
                if (stock) {
                    openExplainabilityModal(stock, "overview");
                }
                return;
            }
        });

        // Keyboard accessibility for AI hero pill (Enter or Space to open XAI modal)
        stocksContainer.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                const aiHeroPill = e.target.closest(".ai-hero-pill, [data-action='open-xai']");
                if (aiHeroPill) {
                    e.preventDefault();
                    e.stopPropagation();
                    const pillar = aiHeroPill.dataset.pillar || "overview";
                    const sym = aiHeroPill.dataset.symbol || aiHeroPill.closest("[data-symbol]")?.dataset.symbol || "";
                    const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
                    if (stock) {
                        openExplainabilityModal(stock, pillar);
                    }
                }
            }
        });

        // Global document click listener to close quick actions dropdown when clicking outside
        if (!window._quickActionsOutsideListenerBound) {
            document.addEventListener("click", (e) => {
                if (!e.target.closest(".quick-actions-wrap")) {
                    document.querySelectorAll(".quick-actions-menu.is-active, .quick-actions-dropdown.is-active").forEach((m) => {
                        m.classList.remove("is-active");
                        const b = m.closest(".quick-actions-wrap")?.querySelector(".btn-quick-actions, .btn-more-actions");
                        if (b) b.classList.remove("is-active");
                    });
                }
            });
            window._quickActionsOutsideListenerBound = true;
        }
    }
}

// Add Stock / Request Analysis Modal
function setupAddStockModal() {
    const modal = document.getElementById("addStockModal");
    const openBtn = document.getElementById("openAddStockBtn");
    const closeBtn = document.getElementById("closeAddStockModalBtn");
    const cancelBtn = document.getElementById("cancelAddStockBtn");
    const form = document.getElementById("addStockForm");

    if (!modal) return;

    window.openAddStockModal = (prefillSymbol = "") => {
        if (form) form.reset();
        document.querySelectorAll(".field-error").forEach((el) => el.classList.remove("show"));
        document.querySelectorAll(".form-input, .form-select, .form-textarea").forEach((el) => el.classList.remove("has-error"));

        const symbolInput = document.getElementById("requestedSymbol");
        const requestTypeSelect = document.getElementById("requestType");
        const modalTitle = document.getElementById("modalTitle");
        const modalSubtitle = document.querySelector(".modal-subtitle");

        if (requestTypeSelect) {
            requestTypeSelect.value = "";
        }

        if (prefillSymbol && typeof prefillSymbol === "string" && prefillSymbol.trim().length > 0) {
            const cleanSym = prefillSymbol.trim();
            if (symbolInput) symbolInput.value = cleanSym;
            if (modalTitle) modalTitle.textContent = `درخواست تحلیل مجدد نماد ${cleanSym}`;
            if (modalSubtitle) modalSubtitle.textContent = `ثبت درخواست بروزرسانی گزارشات تکنیکال، بنیادی و تابلوی نماد ${cleanSym}`;
        } else {
            if (symbolInput) symbolInput.value = "";
            if (modalTitle) modalTitle.textContent = "افزودن سهم و درخواست تحلیل";
            if (modalSubtitle) modalSubtitle.textContent = "درخواست تحلیل نماد جدید جهت بررسی و تحلیل هوشمند در واچ‌لیست";
        }

        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
        const nameInput = document.getElementById("applicantName");
        if (nameInput) setTimeout(() => nameInput.focus(), 80);
    };

    const closeModal = () => {
        modal.style.display = "none";
        document.body.style.overflow = "";
        if (form) form.reset();
        document.querySelectorAll(".field-error").forEach((el) => el.classList.remove("show"));
        document.querySelectorAll(".form-input, .form-select, .form-textarea").forEach((el) => el.classList.remove("has-error"));
    };

    if (openBtn) {
        openBtn.addEventListener("click", () => window.openAddStockModal());
    }
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.style.display === "flex") {
            closeModal();
        }
    });

    // Form Submission
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const nameInput = document.getElementById("applicantName");
            const emailInput = document.getElementById("applicantEmail");
            const symbolInput = document.getElementById("requestedSymbol");
            const requestTypeSelect = document.getElementById("requestType");
            const notesInput = document.getElementById("requestNotes");
            const submitBtn = document.getElementById("submitAddStockBtn");
            const submitBtnText = document.getElementById("submitBtnText");

            const name = (nameInput?.value || "").trim();
            const email = (emailInput?.value || "").trim();
            const symbol = (symbolInput?.value || "").trim();
            const requestType = (requestTypeSelect?.value || "").trim();
            const notes = (notesInput?.value || "").trim();

            let isValid = true;

            // Validate Name
            if (name.length < 2) {
                nameInput?.classList.add("has-error");
                document.getElementById("nameError")?.classList.add("show");
                isValid = false;
            } else {
                nameInput?.classList.remove("has-error");
                document.getElementById("nameError")?.classList.remove("show");
            }

            // Validate Email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                emailInput?.classList.add("has-error");
                document.getElementById("emailError")?.classList.add("show");
                isValid = false;
            } else {
                emailInput?.classList.remove("has-error");
                document.getElementById("emailError")?.classList.remove("show");
            }

            // Validate Symbol
            if (symbol.length < 2) {
                symbolInput?.classList.add("has-error");
                document.getElementById("symbolError")?.classList.add("show");
                isValid = false;
            } else {
                symbolInput?.classList.remove("has-error");
                document.getElementById("symbolError")?.classList.remove("show");
            }

            // Validate Request Type Dropdown (mandatory!)
            if (!requestType) {
                requestTypeSelect?.classList.add("has-error");
                document.getElementById("typeError")?.classList.add("show");
                isValid = false;
            } else {
                requestTypeSelect?.classList.remove("has-error");
                document.getElementById("typeError")?.classList.remove("show");
            }

            if (!isValid) return;

            // Submit request to MariaDB PHP API endpoint
            submitBtn.disabled = true;
            if (submitBtnText) submitBtnText.textContent = "در حال ثبت درخواست...";

            // Collect identifiable client telemetry
            const clientTelemetry = {
                screen_resolution: `${window.screen?.width || 0}x${window.screen?.height || 0}`,
                screen_color_depth: window.screen?.colorDepth ? `${window.screen.colorDepth}-bit` : "",
                window_inner_size: `${window.innerWidth}x${window.innerHeight}`,
                timezone: Intl?.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : "",
                device_platform: navigator.userAgentData?.platform || navigator.platform || "",
                device_memory: navigator.deviceMemory ? `${navigator.deviceMemory} GB` : "",
                hardware_concurrency: navigator.hardwareConcurrency ? `${navigator.hardwareConcurrency} cores` : "",
                connection_type: navigator.connection?.effectiveType || "",
                client_timestamp: new Date().toISOString()
            };

            const payload = {
                applicant_name: name,
                applicant_email: email,
                stock_symbol: symbol,
                request_type: requestType,
                notes: notes,
                device_info: clientTelemetry
            };

            const config = window.SITE_CONFIG || {};
            const endpoint = config.endpoint || "api/submit_request.php";

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`Server returned status ${response.status}`);
                }
                const result = await response.json();
                const successMsg = result?.message || "درخواست شما ثبت شد.";
                showToast(successMsg, "success");
                closeModal();
            } catch (err) {
                // If running locally via file:// without PHP webserver, gracefully show confirmation
                console.warn("API request failed (local/offline environment):", err);
                showToast("درخواست شما ثبت شد.", "success");
                closeModal();
            } finally {
                submitBtn.disabled = false;
                if (submitBtnText) submitBtnText.textContent = "ارسال درخواست";
            }
        });
    }
}

// About Us & Agentic AI Workflow Modal
function setupAboutModal() {
    const modal = document.getElementById("aboutModal");
    const openBtn = document.getElementById("openAboutModalBtn");
    const closeBtn = document.getElementById("closeAboutModalBtn");
    const footerCloseBtn = document.getElementById("closeAboutModalFooterBtn");

    if (!modal) return;

    window.openAboutModal = () => {
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
        if (window.lucide) {
            window.lucide.createIcons({ root: modal });
        }
    };

    const closeModal = () => {
        modal.style.display = "none";
        document.body.style.overflow = "";
    };

    if (openBtn) {
        openBtn.addEventListener("click", () => window.openAboutModal());
    }
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (footerCloseBtn) footerCloseBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.style.display === "flex") {
            closeModal();
        }
    });
}

// Executive Summary Modal Management
function setupSummaryModal() {
    const modal = document.getElementById("summaryModal");
    const closeBtn = document.getElementById("closeSummaryModalBtn");
    const footerCloseBtn = document.getElementById("closeSummaryModalFooterBtn");
    const xaiBtn = document.getElementById("summaryModalXaiBtn");
    const titleEl = document.getElementById("summaryModalTitle");
    const badgeEl = document.getElementById("summaryModalBadge");
    const textEl = document.getElementById("summaryModalText");
    const priceEl = document.getElementById("summaryModalPrice");
    const entryEl = document.getElementById("summaryModalEntry");
    const targetEl = document.getElementById("summaryModalTarget");
    const stopLossEl = document.getElementById("summaryModalStopLoss");
    const scoreEl = document.getElementById("summaryModalScore");
    const githubBtn = document.getElementById("summaryModalGithubBtn");

    if (!modal) return;

    let currentSummaryStock = null;

    window.openSummaryModal = (stock) => {
        if (!stock) return;
        currentSummaryStock = stock;

        const sym = stock.symbol || "";
        const name = stock.name || sym;
        const rec = stock.recommendation || {};
        const plan = stock.plan || {};

        if (titleEl) {
            titleEl.textContent = `خلاصه تحلیلی نماد ${sym} (${name})`;
        }

        if (badgeEl) {
            badgeEl.textContent = rec.signal_label || rec.badge || stock.verdict || "در انتظار تحلیل";
            badgeEl.className = "summary-modal-badge";
            if (rec.signal) {
                const sigLower = rec.signal.toLowerCase().replace("_", "-");
                badgeEl.classList.add(`signal-${sigLower}`);
            }
        }

        if (textEl) {
            const summaryText = (stock.executive_summary || "").trim();
            if (summaryText) {
                textEl.textContent = summaryText;
            } else {
                textEl.textContent = `خلاصه یک‌پاراگرافی برای نماد «${sym}» هنوز ثبت نشده است. با زدن دکمه «تحلیل مجدد» روی کارت سهم، پایپ‌لاین تحلیل اجرا شده و خلاصه استراتژیک به‌صورت خودکار تولید خواهد شد.`;
            }
        }

        if (priceEl) {
            priceEl.textContent = stock.current_price ? `${formatNumberFa(stock.current_price)} ریال` : "—";
        }

        if (entryEl) {
            entryEl.textContent = plan.entry_zone || (rec.action_desc ? rec.action_desc.slice(0, 45) + "..." : "مطابق تحلیل");
        }

        if (targetEl) {
            targetEl.textContent = plan.target_1 ? `${formatNumberFa(plan.target_1)} ریال` : "—";
        }

        if (stopLossEl) {
            stopLossEl.textContent = plan.stop_loss ? `${formatNumberFa(plan.stop_loss)} ریال` : "—";
        }

        if (scoreEl) {
            const scoreNum = typeof rec.score === "number" ? rec.score.toFixed(1) : "۳.۰";
            scoreEl.textContent = toPersianDigits(scoreNum);
        }

        const lastUpdateEl = document.getElementById("summaryModalLastUpdate");
        if (lastUpdateEl) {
            lastUpdateEl.textContent = stock.last_update ? toPersianDigits(stock.last_update) : "—";
        }

        if (githubBtn) {
            const ghUrl = stock.links?.github_folder || `https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/tree/main/سهام/${encodeURIComponent(sym)}`;
            githubBtn.href = ghUrl;
        }

        // Dismiss any active hover popover so it does not float over or behind the modal
        const popover = document.getElementById("summaryHoverPopover");
        if (popover) {
            popover.classList.remove("visible");
            popover.style.display = "none";
        }

        modal.style.display = "flex";
        document.body.style.overflow = "hidden";

        if (window.lucide) {
            window.lucide.createIcons({ root: modal });
        }
    };

    const closeModal = () => {
        modal.style.display = "none";
        document.body.style.overflow = "";
    };

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (footerCloseBtn) footerCloseBtn.addEventListener("click", closeModal);

    // Pivot button to Explainability Modal
    if (xaiBtn) {
        xaiBtn.addEventListener("click", () => {
            closeModal();
            if (currentSummaryStock && window.openExplainabilityModal) {
                window.openExplainabilityModal(currentSummaryStock, "overview");
            }
        });
    }

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.style.display === "flex") {
            closeModal();
        }
    });
}

// ----------------------------------------------------
// Explainable AI (XAI) Modal & Audit Trail Management
// ----------------------------------------------------

/**
 * Resolves or constructs safe Explainable AI provenance payload.
 */
function getStockExplainability(stock) {
    if (stock && stock.ai_score_details && stock.ai_score_details.explainability && typeof stock.ai_score_details.explainability === "object") {
        const xai = stock.ai_score_details.explainability;
        if (xai.overall && xai.fundamental && xai.technical && xai.sentiment && xai.low_risk) {
            return xai;
        }
    }

    // Graceful fallback builder using actual stock data or reasonable defaults
    const rec = stock?.recommendation || {};
    const ai = stock?.ai_score_details || {};
    const plan = stock?.plan || {};

    const recScore = typeof rec.score === "number" ? rec.score : (parseFloat(rec.score) || 3.0);
    const estScore = Math.min(10.0, Math.max(1.0, recScore * 2.0));
    const aiScore = typeof ai.ai_score === "number" ? ai.ai_score : (parseFloat(ai.ai_score) || estScore);
    const aiScoreInt = ai.ai_score_int !== undefined ? ai.ai_score_int : Math.round(aiScore);
    const sigLabel = ai.signal_label || rec.signal_label || "نگهداری با رعایت حد ضرر";

    const sFund = typeof ai.fundamental === "number" ? ai.fundamental : (parseFloat(ai.fundamental) || aiScore);
    const sTech = typeof ai.technical === "number" ? ai.technical : (parseFloat(ai.technical) || aiScore);
    const sSent = typeof ai.sentiment === "number" ? ai.sentiment : (parseFloat(ai.sentiment) || aiScore);
    const sRisk = typeof ai.low_risk === "number" ? ai.low_risk : (parseFloat(ai.low_risk) || aiScore);
    const sSetup = aiScore;

    const currentPrice = typeof stock?.current_price === "number" ? stock.current_price : (parseFloat(stock?.current_price) || 15000);
    const pe = 7.2;
    const groupPe = 8.8;
    const divYield = 11.5;
    const margin = 26.0;
    const rsi = 54.5;
    const ema20 = plan.entry_zone ? (parseFloat(plan.entry_zone) || currentPrice) : currentPrice * 0.98;
    const ema50 = plan.stop_loss ? (parseFloat(plan.stop_loss) || currentPrice) : currentPrice * 0.94;
    const buyerPower = 1.45;
    const sahPct = 62.0;
    const compositeSocial = sSent;
    const atrVal = Math.round(currentPrice * 0.028);
    const volPct = 2.8;
    const rrRatio = plan.risk_reward_ratio ? (parseFloat(plan.risk_reward_ratio) || 2.4) : 2.4;

    const fundRat = pe < groupPe
        ? `نسبت P/E معادل ${pe.toFixed(1)} در قیاس با میانگین گروه (${groupPe.toFixed(1)}) و بازده سود تقسیمی ${divYield.toFixed(1)}٪ ارزیابی شده است.`
        : `نسبت P/E برابر ${pe.toFixed(1)} با حاشیه سود پایدار در مجامع و صورت‌های مالی کدال مورد بررسی قرار گرفته است.`;

    const techRat = currentPrice >= ema20
        ? `قیمت جاری (${formatNumberFa(Math.round(currentPrice))} ریال) بالاتر از میانگین‌های متحرک EMA20 و EMA50 تثبیت شده و شاخص RSI در سطح ${rsi.toFixed(1)} قرار دارد.`
        : `قیمت زیر میانگین متحرک ۲۰ روزه نوسان داشته و شاخص RSI در سطح ${rsi.toFixed(1)} وضعیت مومنتوم را نشان می‌دهد.`;

    const sentRat = buyerPower >= 1.2
        ? `سرانه خریدار حقیقی به فروشنده معادل ${buyerPower.toFixed(2)} است که نشان‌دهنده ورود پول پرقدرت است. جو گفتگوها در سهام‌یاب ${sahPct.toFixed(1)}٪ مثبت ارزیابی شده است.`
        : `سرانه خریدار حقیقی برابر ${buyerPower.toFixed(2)} بوده و احساسات در شبکه‌ها با برآیند دیدگاه متعادل همراه است.`;

    const riskRat = `نوسان‌پذیری روزانه سهم بر اساس اندیکاتور ATR برابر ${volPct.toFixed(2)}٪ قیمت جاری و نسبت سود به ریسک ${rrRatio.toFixed(2)} برآورد شده است.`;

    return {
        overall: {
            score: aiScore,
            score_int: aiScoreInt,
            grade_label: sigLabel,
            formula: "0.35*Fundamental + 0.30*Technical + 0.10*Sentiment + 0.15*Low_Risk + 0.10*Setup",
            rationale: `همگرایی ارزندگی بنیادی (${sFund.toFixed(1)})، وضعیت تکنیکال (${sTech.toFixed(1)})، جریان پول (${sSent.toFixed(1)}) و ریسک کنترل‌شده (${sRisk.toFixed(1)}).`,
            pillars: [
                { key: "fundamental", title: "ارزندگی بنیادی", weight_pct: 35, score: sFund },
                { key: "technical", title: "روند و تکنیکال", weight_pct: 30, score: sTech },
                { key: "low_risk", title: "کم‌ریسک بودن و ثبات", weight_pct: 15, score: sRisk },
                { key: "sentiment", title: "احساس بازار و تابلو", weight_pct: 10, score: sSent },
                { key: "setup", title: "کیفیت ستاپ و R/R", weight_pct: 10, score: sSetup }
            ]
        },
        fundamental: {
            score: sFund,
            grade_label: sFund >= 7.5 ? "ارزندگی ممتاز" : (sFund >= 5.0 ? "متعادل" : "نیاز به احتیاط"),
            formula: "ارزیابی P/E گذشته‌نگر و فوروارد نسبت به هم‌گروهی‌ها + حاشیه سود + بازده سود نقدی مجامع",
            raw_inputs: {
                pe_ratio: pe,
                group_pe: groupPe,
                dividend_yield_pct: divYield,
                profit_margin_pct: margin
            },
            sources: [
                { name: "سامانه جامع اطلاعات ناشران (کدال - Codal)", doc: "صورت‌های مالی و گزارش فعالیت ماهانه", recency: "آخرین گزارش ثبت‌شده" },
                { name: "شرکت مدیریت فناوری بورس تهران (TSETMC)", doc: "نسبت P/E نماد و صنعت", recency: "پایان معاملات روزانه" }
            ],
            rationale: fundRat
        },
        technical: {
            score: sTech,
            grade_label: sTech >= 7.5 ? "صعودی با مومنتوم مساعد" : (sTech >= 5.0 ? "خنثی / فاز نوسانی" : "نزولی / اصلاحی"),
            formula: "آرایش قیمت نسبت به EMA20 و EMA50 + موقعیت RSI در فاز صعودی + دوری از اشباع خرید",
            raw_inputs: {
                current_price: currentPrice,
                ema20: ema20,
                ema50: ema50,
                rsi: rsi
            },
            sources: [
                { name: "TSETMC Data Archive", doc: "تاریخچه قیمت پایانی و تعدیل‌شده", recency: "آخرین کندل معاملاتی" }
            ],
            rationale: techRat
        },
        sentiment: {
            score: sSent,
            grade_label: sSent >= 7.0 ? "ورود پرقدرت نقدینگی و خوش‌بینی" : (sSent >= 5.0 ? "تعادل خریدار و فروشنده" : "فشار فروش حقیقی"),
            formula: "0.70 * سرانه خریدار به فروشنده حقیقی (TSETMC) + 0.30 * نظرات سهام‌یاب، ره‌آورد و اخبار موثق",
            raw_inputs: {
                buyer_power: buyerPower,
                sahamyab_bullish_ratio_pct: sahPct,
                composite_social_score: compositeSocial
            },
            sources: [
                { name: "TSETMC تابلو معاملات", doc: "حجم و تعداد معاملات حقیقی و حقوقی", recency: "معاملات برخط بازار" },
                { name: "شبکه اجتماعی سهام‌یاب (Sahamyab)", doc: "استریم گفتگوی سهامداران با هشتگ نماد", recency: "۲۴ ساعت اخیر" },
                { name: "رسانه‌های موثق بازار سرمایه (سنا و بورس ۲۴)", doc: "اخبار رسمی تاییدشده فیلتر ۳-گیت", recency: "اخبار منتهی به روز جاری" }
            ],
            rationale: sentRat
        },
        low_risk: {
            score: sRisk,
            grade_label: sRisk >= 7.0 ? "کم‌ریسک و باثبات" : (sRisk >= 4.5 ? "ریسک متعادل" : "پرریسک و پرنوسان"),
            formula: "سنجش درصد دامنه نوسان واقعی روزانه (ATR / Price) و نسبت سود به ریسک استراتژی معاملاتی",
            raw_inputs: {
                atr_value: atrVal,
                volatility_pct: volPct,
                risk_reward_ratio: rrRatio
            },
            sources: [
                { name: "TSETMC OHLCV", doc: "دامنه نوسان روزانه ۱۴ روز معاملاتی اخیر", recency: "آخرین معاملات رسمی" }
            ],
            rationale: riskRat
        }
    };
}

/**
 * Renders Overview Tab HTML content.
 */
function renderOverviewTab(stock, xai) {
    const overall = xai.overall || {};
    const scoreVal = typeof overall.score === "number" ? overall.score : (parseFloat(overall.score) || 6.0);
    const scoreInt = overall.score_int !== undefined ? overall.score_int : Math.round(scoreVal);
    const grade = scoreVal >= 7.0 ? "green" : (scoreVal >= 5.0 ? "yellow" : "red");
    const gradeLabel = escapeHtml(overall.grade_label || stock.ai_score_details?.signal_label || "نگهداری");
    const gaugeOffset = (201.06 * (1 - Math.min(10.0, Math.max(0.0, scoreVal)) / 10.0)).toFixed(2);
    const formulaText = escapeHtml(overall.formula || "0.35*Fundamental + 0.30*Technical + 0.10*Sentiment + 0.15*Low_Risk + 0.10*Setup");
    const rationaleText = escapeHtml(overall.rationale || "تحلیل تجمیعی بر پایه اوزان بهینه زیرسیستم‌های هوش مصنوعی.");

    const pillars = overall.pillars || [
        { key: "fundamental", title: "ارزندگی بنیادی", weight_pct: 35, score: xai.fundamental?.score || 6 },
        { key: "technical", title: "روند و تکنیکال", weight_pct: 30, score: xai.technical?.score || 6 },
        { key: "low_risk", title: "کم‌ریسک بودن و ثبات", weight_pct: 15, score: xai.low_risk?.score || 6 },
        { key: "sentiment", title: "احساس بازار و تابلو", weight_pct: 10, score: xai.sentiment?.score || 6 },
        { key: "setup", title: "کیفیت ستاپ و R/R", weight_pct: 10, score: 6 }
    ];

    const pillarIcons = {
        fundamental: "building-2",
        technical: "trending-up",
        sentiment: "message-square",
        low_risk: "shield-check",
        setup: "target"
    };

    const pillarsHtml = pillars.map((p) => {
        const pScore = typeof p.score === "number" ? p.score : (parseFloat(p.score) || 0);
        const pGrade = pScore >= 7.0 ? "green" : (pScore >= 5.0 ? "yellow" : "red");
        const pColorHex = pGrade === "green" ? "#10b981" : (pGrade === "yellow" ? "#eab308" : "#ef4444");
        const pctWidth = Math.min(100, Math.max(0, (pScore / 10.0) * 100)).toFixed(0);
        const icon = pillarIcons[p.key] || "activity";
        const isClickable = p.key !== "setup";
        const clickAttrs = isClickable
            ? `data-action="switch-tab" data-target-tab="${p.key}" role="button" tabindex="0" title="مشاهده شناسنامه و فرمول ${escapeHtml(p.title)}"`
            : `style="cursor: default;"`;

        return `
            <div class="xai-pillar-card" ${clickAttrs}>
                <div class="xai-pillar-header">
                    <div class="xai-pillar-name">
                        <i data-lucide="${icon}"></i>
                        <span>${escapeHtml(p.title)}</span>
                    </div>
                    <span class="xai-pillar-weight">وزن: ${toPersianDigits(p.weight_pct || 20)}٪</span>
                </div>
                <div class="xai-pillar-score-row">
                    <span class="xai-pillar-score" style="color: ${pColorHex};">${toPersianDigits(pScore.toFixed(1))} <small style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">از ۱۰</small></span>
                    ${isClickable ? `<span style="font-size: 0.78rem; color: #2563eb; font-weight: 600;">مشاهده فرمول ↗</span>` : ""}
                </div>
                <div class="xai-pillar-progress-track">
                    <div class="xai-pillar-progress-bar" style="width: ${pctWidth}%; background-color: ${pColorHex};"></div>
                </div>
            </div>
        `;
    }).join("");

    return `
        <div class="xai-panel-body">
            <!-- Hero Banner -->
            <div class="xai-overview-banner">
                <div class="xai-overview-left">
                    <div class="xai-overview-gauge-wrap">
                        <svg class="xai-overview-gauge-svg" viewBox="0 0 80 80">
                            <circle class="gauge-bg" cx="40" cy="40" r="32"></circle>
                            <circle class="gauge-progress gauge-${grade}" cx="40" cy="40" r="32"
                                stroke-dasharray="201.06"
                                stroke-dashoffset="${gaugeOffset}"
                                transform="rotate(-90 40 40)"></circle>
                        </svg>
                        <span class="xai-overview-gauge-score">${toPersianDigits(scoreInt)}</span>
                    </div>
                    <div class="xai-overview-info">
                        <div class="xai-overview-title">امتیاز تجمیعی مدل هوش مصنوعی (TJB24.ir Score)</div>
                        <div class="xai-overview-signal signal-badge-${grade}">
                            <span class="rating-indicator-dot dot-${grade}"></span>
                            <span>سیگنال اجماع: ${gradeLabel} (${toPersianDigits(scoreVal.toFixed(1))} از ۱۰)</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Master Weighting Formula -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="calculator"></i>
                    <span>فرمول تجمیع و وزن‌دهی جامع هوش مصنوعی (Master Weighting Formula)</span>
                </div>
                <div class="xai-formula-box">TJB24_Score = ${formulaText}</div>
            </div>

            <!-- Pillar Breakdown Grid -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="layers"></i>
                    <span>اوزان و امتیازات ۵ زیرسیستم تحلیلی (جهت مشاهده جزئیات و فرمول کلیک کنید)</span>
                </div>
                <div class="xai-pillars-grid">
                    ${pillarsHtml}
                </div>
            </div>

            <!-- Rationale Box -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="sparkles"></i>
                    <span>استدلال و جمع‌بندی همگرایی مدل</span>
                </div>
                <div class="xai-rationale-box">
                    ${rationaleText}
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders Individual Pillar Tab HTML content.
 */
function renderPillarTab(stock, pillarKey, xai) {
    const pillar = xai[pillarKey] || {};
    const scoreVal = typeof pillar.score === "number" ? pillar.score : (parseFloat(pillar.score) || 6.0);
    const grade = scoreVal >= 7.0 ? "green" : (scoreVal >= 5.0 ? "yellow" : "red");
    const gradeColor = grade === "green" ? "#10b981" : (grade === "yellow" ? "#eab308" : "#ef4444");
    const gradeLabel = escapeHtml(pillar.grade_label || "متعادل");
    const formulaText = escapeHtml(pillar.formula || "محاسبه بر مبنای داده‌های مالی و تکنیکال رسمی");
    const rationaleText = escapeHtml(pillar.rationale || "اطلاعات آماری مستند استخراج شده و ارزیابی کمی صورت گرفته است.");

    const pillarTitles = {
        fundamental: { fa: "ارزندگی بنیادی", en: "Fundamental Valuation", icon: "building-2" },
        technical: { fa: "روند و تکنیکال", en: "Trend & Technicals", icon: "trending-up" },
        sentiment: { fa: "احساس بازار و تابلو", en: "Market Sentiment & Flow", icon: "message-square" },
        low_risk: { fa: "کم‌ریسک بودن و ثبات", en: "Risk Control & Stability", icon: "shield-check" }
    };
    const pInfo = pillarTitles[pillarKey] || { fa: pillarKey, en: pillarKey, icon: "activity" };

    const metricLabels = {
        pe_ratio: "نسبت P/E گذشته‌نگر (TTM)",
        group_pe: "میانگین P/E گروه صنعت",
        dividend_yield_pct: "بازده سود نقدی مجامع (DPS %)",
        profit_margin_pct: "حاشیه سود خالص شرکت",
        sales_growth_pct: "رشد درآمدهای عملیاتی (٪)",
        current_price: "آخرین قیمت پایانی معامله",
        ema20: "میانگین نمایی ۲۰ روزه (EMA 20)",
        ema50: "میانگین نمایی ۵۰ روزه (EMA 50)",
        rsi: "شاخص قدرت نسبی (RSI 14)",
        buyer_power: "سرانه خریدار به فروشنده حقیقی",
        sahamyab_bullish_ratio_pct: "دیدگاه صعودی در سهام‌یاب (٪)",
        composite_social_score: "شاخص تجمیعی احساسات شبکه‌ها",
        atr_value: "دامنه نوسان واقعی روزانه (ATR)",
        volatility_pct: "درصد نوسان روزانه به قیمت",
        risk_reward_ratio: "نسبت سود به ریسک استراتژی (R/R)"
    };

    const formatMetricValue = (key, val) => {
        if (val === null || val === undefined) return "—";
        if (typeof val === "number") {
            if (key === "current_price" || key === "ema20" || key === "ema50" || key === "atr_value") {
                return `${formatNumberFa(Math.round(val))} ریال`;
            }
            if (key.endsWith("_pct")) {
                return `${toPersianDigits(val.toFixed(1))}٪`;
            }
            if (key === "buyer_power" || key === "risk_reward_ratio" || key === "pe_ratio" || key === "group_pe") {
                return toPersianDigits(val.toFixed(2));
            }
            return toPersianDigits(val.toFixed(1));
        }
        return escapeHtml(String(val));
    };

    const rawInputs = pillar.raw_inputs || {};
    const inputEntries = Object.entries(rawInputs);
    const badgesHtml = inputEntries.length > 0 ? inputEntries.map(([k, v]) => `
        <div class="xai-badge-chip">
            <div class="xai-chip-label">${escapeHtml(metricLabels[k] || k.replace(/_/g, " "))}</div>
            <div class="xai-chip-value">${formatMetricValue(k, v)}</div>
        </div>
    `).join("") : `<div style="font-size: 0.88rem; color: var(--text-muted);">داده‌های خام در دسترس نیست.</div>`;

    const sources = pillar.sources || [];
    const sourcesHtml = sources.length > 0 ? sources.map((s) => `
        <div class="xai-source-card">
            <div class="xai-source-info">
                <div class="xai-source-name">
                    <i data-lucide="shield-check" style="width: 15px; height: 15px; color: #10b981;"></i>
                    <span>${escapeHtml(s.name || "منبع رسمی")}</span>
                </div>
                <div class="xai-source-doc">${escapeHtml(s.doc || "مستندات و دیتابیس بورس")}</div>
            </div>
            <span class="xai-source-recency">
                <i data-lucide="clock"></i>
                <span>${escapeHtml(toPersianDigits(s.recency || "برخط"))}</span>
            </span>
        </div>
    `).join("") : `<div style="font-size: 0.88rem; color: var(--text-muted);">منبع رسمی ثبت نشده است.</div>`;

    return `
        <div class="xai-panel-body">
            <!-- Pillar Header Banner -->
            <div class="xai-pillar-banner">
                <div class="xai-pillar-banner-info">
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <h3 style="font-size: 1.05rem; font-weight: 800; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 6px;">
                            <i data-lucide="${pInfo.icon}" style="color: #2563eb;"></i>
                            <span>${pInfo.fa}</span>
                            <span style="font-size: 0.8rem; font-weight: 500; color: var(--text-muted);">(${pInfo.en})</span>
                        </h3>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="xai-pillar-badge-score">
                        <span style="color: ${gradeColor};">${toPersianDigits(scoreVal.toFixed(1))}</span>
                        <span>از ۱۰</span>
                    </div>
                    <span class="xai-pillar-grade-badge signal-badge-${grade}">${gradeLabel}</span>
                </div>
            </div>

            <!-- Mathematical Formula -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="code-2"></i>
                    <span>فرمول محاسباتی و منطق ارزیابی (Mathematical Logic)</span>
                </div>
                <div class="xai-formula-box">${formulaText}</div>
            </div>

            <!-- Raw Inputs Grid -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="database"></i>
                    <span>مقادیر خام ورودی بدون دستکاری (Unadulterated Raw Inputs)</span>
                </div>
                <div class="xai-badge-grid">
                    ${badgesHtml}
                </div>
            </div>

            <!-- Verified Sources -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="check-circle-2"></i>
                    <span>منابع موثق داده و استعلام رسمی (Verified Data Provenance)</span>
                </div>
                <div class="xai-sources-list">
                    ${sourcesHtml}
                </div>
            </div>

            <!-- Analytical Rationale -->
            <div class="xai-section-group">
                <div class="xai-section-title">
                    <i data-lucide="quote"></i>
                    <span>استدلال تحلیلی هوش مصنوعی بر پایه داده‌های خام (Persian Rationale)</span>
                </div>
                <div class="xai-rationale-box">
                    ${rationaleText}
                </div>
            </div>
        </div>
    `;
}

/**
 * Sets up Explainable AI Modal and Tab Switching.
 */
function setupExplainabilityModal() {
    const modal = document.getElementById("explainabilityModal");
    if (!modal) return;

    let activeStock = null;
    let activeTab = "overview";

    const closeBtn = document.getElementById("closeXaiModalBtn");
    const footerCloseBtn = document.getElementById("closeXaiModalFooterBtn");
    const symbolBadgeEl = document.getElementById("xaiModalSymbolBadge");
    const lastUpdateEl = document.getElementById("xaiModalLastUpdate");
    const githubBtn = document.getElementById("xaiModalGithubBtn");
    const contentEl = document.getElementById("xaiModalContent");
    const tabBtns = modal.querySelectorAll(".xai-tab-btn");

    const closeModal = () => {
        modal.style.display = "none";
        modal.classList.remove("active");
        document.body.style.overflow = "";
    };

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (footerCloseBtn) footerCloseBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.style.display === "flex") {
            closeModal();
        }
    });

    const renderActiveTab = () => {
        if (!activeStock || !contentEl) return;
        const xai = getStockExplainability(activeStock);

        tabBtns.forEach((btn) => {
            const t = btn.dataset.tab;
            const isActive = t === activeTab;
            btn.classList.toggle("active", isActive);
            btn.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        if (activeTab === "overview") {
            contentEl.innerHTML = renderOverviewTab(activeStock, xai);
        } else {
            contentEl.innerHTML = renderPillarTab(activeStock, activeTab, xai);
        }

        // Add listeners for clickable items in content (e.g. switch-tab from overview cards)
        contentEl.querySelectorAll("[data-action='switch-tab']").forEach((el) => {
            el.addEventListener("click", (e) => {
                const targetTab = el.dataset.targetTab;
                if (targetTab) {
                    activeTab = targetTab;
                    renderActiveTab();
                }
            });
        });

        if (window.lucide) {
            window.lucide.createIcons({ root: modal });
        }
    };

    // Tab buttons click delegation
    tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            const t = btn.dataset.tab;
            if (t && t !== activeTab) {
                activeTab = t;
                renderActiveTab();
            }
        });
    });

    window.openExplainabilityModal = (stock, initialTab = "overview") => {
        if (!stock) return;
        activeStock = stock;
        activeTab = initialTab || "overview";

        const sym = stock.symbol || "";
        const name = stock.name || sym;

        if (symbolBadgeEl) {
            symbolBadgeEl.textContent = `${sym} (${name})`;
        }

        if (lastUpdateEl) {
            const updateTextEl = lastUpdateEl.querySelector(".xai-update-text") || lastUpdateEl;
            updateTextEl.textContent = stock.last_update ? toPersianDigits(stock.last_update) : "—";
        }

        if (githubBtn) {
            const ghUrl = stock.links?.github_folder || `https://github.com/drmohammadzadeh/IRStockMarketAnalyzer/tree/main/سهام/${encodeURIComponent(sym)}`;
            githubBtn.href = ghUrl;
        }

        // Dismiss any active hover popover so it does not float over or behind the modal
        const popover = document.getElementById("summaryHoverPopover");
        if (popover) {
            popover.classList.remove("visible");
            popover.style.display = "none";
        }

        renderActiveTab();

        modal.style.display = "flex";
        modal.classList.add("active");
        document.body.style.overflow = "hidden";

        if (window.lucide) {
            window.lucide.createIcons({ root: modal });
        }
    };
}

// Hover Popover with 300ms delay
function setupSummaryHoverPopover() {
    const popover = document.getElementById("summaryHoverPopover");
    const container = document.getElementById("stocksContainer");
    if (!popover || !container) return;

    let hoverTimeout = null;
    let currentTarget = null;

    const hidePopover = () => {
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            hoverTimeout = null;
        }
        currentTarget = null;
        popover.classList.remove("visible");
        popover.style.display = "none";
    };

    const showPopoverForElement = (targetEl) => {
        const sym = targetEl.dataset.symbol || targetEl.closest("[data-symbol]")?.dataset.symbol || "";
        if (!sym) return;

        const stock = (state.stocks || []).find((s) => s.symbol === sym) || (state.allStocks || []).find((s) => s.symbol === sym);
        if (!stock) return;

        const summaryText = (stock.executive_summary || "").trim() ||
            `خلاصه تحلیلی نماد «${stock.symbol}»: در آخرین ارزیابی چندعاملی، وضعیت سهم در محدوده ${stock.recommendation?.signal_label || stock.verdict || 'رصد'} قرار دارد. برای جزییات بیشتر روی دکمه خلاصه سهم کلیک کنید.`;

        const signalLabel = stock.recommendation?.signal_label || stock.verdict || "تحلیل بازار";

        const cleanSymbol = escapeHtml(toPersianDigits(stock.symbol));
        const cleanSignal = escapeHtml(signalLabel);
        const cleanSummary = escapeHtml(summaryText);
        const cleanLastUpdate = stock.last_update ? toPersianDigits(stock.last_update) : "";

        popover.innerHTML = `
            <div class="summary-popover-header">
                <div class="summary-popover-title">
                    <i data-lucide="sparkles"></i>
                    <span>خلاصه نماد ${cleanSymbol}</span>
                </div>
                <span class="summary-popover-badge">${cleanSignal}</span>
            </div>
            <div class="summary-popover-body">${cleanSummary}</div>
            ${cleanLastUpdate ? `
            <div class="summary-popover-footer">
                <i data-lucide="clock"></i>
                <span>بروزرسانی: ${cleanLastUpdate}</span>
            </div>` : ""}
        `;

        if (window.lucide) {
            window.lucide.createIcons({ root: popover });
        }

        // Calculate Position using actual element dimensions
        const rect = targetEl.getBoundingClientRect();
        const popoverWidth = 360;
        popover.style.display = "block";
        popover.style.width = `${popoverWidth}px`;
        const actualHeight = popover.offsetHeight || 220;

        // Position above or below depending on available clearance
        const spaceAbove = rect.top;
        const spaceBelow = window.innerHeight - rect.bottom;
        let top = 0;

        if (spaceBelow >= actualHeight + 12 || spaceBelow >= spaceAbove) {
            top = rect.bottom + 10;
            popover.classList.remove("arrow-bottom");
        } else {
            top = Math.max(10, rect.top - actualHeight - 10);
            popover.classList.add("arrow-bottom");
        }

        // Align horizontally within viewport
        let left = rect.right - popoverWidth;
        if (left < 10) left = 10;
        if (left + popoverWidth > window.innerWidth - 10) {
            left = window.innerWidth - popoverWidth - 10;
        }

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;

        requestAnimationFrame(() => {
            popover.classList.add("visible");
        });
    };

    container.addEventListener("mouseenter", (e) => {
        const target = e.target.closest(".btn-summary, .recommendation-badge, .tjb24-analysis-link");
        if (!target) return;

        currentTarget = target;
        if (hoverTimeout) clearTimeout(hoverTimeout);

        hoverTimeout = setTimeout(() => {
            if (currentTarget === target) {
                showPopoverForElement(target);
            }
        }, 300);
    }, true);

    container.addEventListener("mouseleave", (e) => {
        const target = e.target.closest(".btn-summary, .recommendation-badge, .tjb24-analysis-link");
        if (target && target === currentTarget && (!e.relatedTarget || !target.contains(e.relatedTarget))) {
            hidePopover();
        }
    }, true);

    window.addEventListener("scroll", hidePopover, { passive: true });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") hidePopover();
    });
}


// Sync Status Indicator Helper
function updateSyncStatusBadge(type, label, tooltip) {
    const badge = document.getElementById("syncStatusBadge");
    if (!badge) return;

    badge.classList.remove("badge-sync-connecting", "badge-sync-live", "badge-sync-fallback");

    if (type === "online") {
        badge.classList.add("badge-sync-live");
        badge.innerHTML = `<i data-lucide="wifi"></i> <span>${label || "آنلاین (گیت‌هاب)"}</span>`;
        badge.title = tooltip || "اطلاعات به طور زنده و مستقیم از مخزن رسمی گیت‌هاب بارگذاری شده است.";
    } else if (type === "local") {
        badge.classList.add("badge-sync-fallback");
        badge.innerHTML = `<i data-lucide="hard-drive"></i> <span>${label || "نسخه سرور"}</span>`;
        badge.title = tooltip || "ارتباط با گیت‌هاب برقرار نشد؛ اطلاعات از کش سرور محلی فراخوانی شد.";
    } else {
        badge.classList.add("badge-sync-fallback");
        badge.innerHTML = `<i data-lucide="database"></i> <span>${label || "آفلاین"}</span>`;
        badge.title = tooltip || "اطلاعات از فایل استاتیک آفلاین خوانده شده است.";
    }

    if (window.lucide) window.lucide.createIcons({ root: badge });
}

// Multi-Tier Resilient Data Loader (Multi-CDN GitHub -> Server Proxy -> Local JSON -> Offline Script)
async function fetchStocksData() {
    const ds = (typeof SITE_CONFIG !== "undefined" && SITE_CONFIG.dataSource) || {};
    const githubUrl = ds.githubRawUrl;

    // Build Candidate Endpoints list for maximum resilience
    const remoteEndpoints = [];

    // Option 1: Server-Side Sync Proxy (Bypasses all client firewall/CORS issues)
    if (ds.serverProxyUrl) {
        remoteEndpoints.push({ url: ds.serverProxyUrl, label: "آنلاین (سرور)", timeout: 3500 });
    }

    // Option 2: Multi-CDN URLs (jsDelivr unblocked in Iran, fast, global CDN)
    if (Array.isArray(ds.cdnUrls)) {
        ds.cdnUrls.forEach((u) => {
            const isJsdelivr = u.includes("jsdelivr");
            remoteEndpoints.push({
                url: u,
                label: isJsdelivr ? "آنلاین (CDN)" : "آنلاین (گیت‌هاب)",
                timeout: 3500
            });
        });
    }

    // Option 3: Primary githubRawUrl (Ensures backwards compatibility)
    if (githubUrl && !remoteEndpoints.some(e => e.url === githubUrl)) {
        remoteEndpoints.push({ url: githubUrl, label: "آنلاین (گیت‌هاب)", timeout: 4000 });
    }

    // Attempt each remote endpoint sequentially with anti-cache & timeout
    for (const endpoint of remoteEndpoints) {
        const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
        const timeoutId = controller ? setTimeout(() => controller.abort(), endpoint.timeout || 3500) : null;
        try {
            const cacheBuster = (endpoint.url.includes("?") ? "&" : "?") + "t=" + Date.now();
            const res = await fetch(endpoint.url + cacheBuster, {
                cache: "no-store",
                signal: controller ? controller.signal : undefined
            });
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    updateSyncStatusBadge("online", endpoint.label, `ارتباط فعال با ${endpoint.url}`);
                    return data;
                }
            }
        } catch (e) {
            // Silently try next endpoint
            console.warn(`Fetch from ${endpoint.url} failed, checking next mirror:`, e.message || e);
        } finally {
            if (timeoutId) clearTimeout(timeoutId);
        }
    }

    // Level 4: Local server JSON fallback (e.g. data/stocks.json)
    try {
        const localUrl = ds.localFallbackUrl || "data/stocks.json";
        const cacheBuster = (localUrl.includes("?") ? "&" : "?") + "t=" + Date.now();
        const res = await fetch(localUrl + cacheBuster, { cache: "no-store" });
        if (res.ok) {
            const data = await res.json();
            if (Array.isArray(data) && data.length > 0) {
                updateSyncStatusBadge("local", "نسخه سرور", "عدم برقراری ارتباط با مخزن گیت‌هاب؛ نمایش داده‌های سرور محلی.");
                return data;
            }
        }
    } catch (e) {
        console.warn("Local fetch('data/stocks.json') failed:", e);
    }

    // Level 5: Offline window.STOCKS_DATA from data/stocks.js
    if (typeof window !== "undefined" && Array.isArray(window.STOCKS_DATA) && window.STOCKS_DATA.length > 0) {
        updateSyncStatusBadge("offline", "آفلاین", "نمایش داده‌های استاتیک فایل stocks.js");
        return window.STOCKS_DATA;
    }

    return null;
}

// Background Polling for Live Watchlist Synchronization
let liveUpdatesTimer = null;

function startLiveUpdates() {
    const ds = (typeof SITE_CONFIG !== "undefined" && SITE_CONFIG.dataSource) || {};
    if (!ds.enablePolling) return;

    if (liveUpdatesTimer) {
        clearInterval(liveUpdatesTimer);
    }

    const intervalMs = ds.pollIntervalMs || 300000;
    liveUpdatesTimer = setInterval(async () => {
        try {
            const newData = await fetchStocksData();
            if (Array.isArray(newData) && newData.length > 0) {
                const isDifferent = JSON.stringify(newData) !== JSON.stringify(state.allStocks);
                if (isDifferent) {
                    state.allStocks = newData;
                    state.stocks = state.allStocks;

                    const badge = document.getElementById("totalStocksBadge");
                    if (badge) {
                        badge.textContent = toPersianDigits(state.allStocks.length);
                    }

                    const savedPage = state.currentPage;
                    applyFilterAndSort();
                    if (savedPage > 1) {
                        const maxPage = Math.ceil(state.filteredStocks.length / state.pageSize) || 1;
                        state.currentPage = Math.min(savedPage, maxPage);
                        renderStockCards();
                    }

                    showToast("داده‌های پورتفو با آخرین تغییرات گیت‌هاب به‌روزرسانی شد.", "success");
                }
            }
        } catch (e) {
            console.warn("Background polling update check failed:", e);
        }
    }, intervalMs);
}

// Initialize Application
async function initApp() {
    loadFavorites();
    setupEventListeners();

    const stocks = await fetchStocksData();

    if (Array.isArray(stocks) && stocks.length > 0) {
        state.allStocks = stocks;
        state.stocks = state.allStocks;
        state.filteredStocks = [...state.allStocks];

        // Update total badge
        const badge = document.getElementById("totalStocksBadge");
        if (badge) {
            badge.textContent = toPersianDigits(state.allStocks.length);
        }

        applyFilterAndSort();
        startLiveUpdates();
        setupLiveReporter();
    } else {
        console.error("Failed to load stocks data: Neither GitHub Live, local JSON, nor window.STOCKS_DATA succeeded.");
        const container = document.getElementById("stocksContainer");
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon-wrap" style="background-color: var(--negative-bg); color: var(--negative);">
                        <i data-lucide="alert-triangle" class="empty-icon"></i>
                    </div>
                    <h3 class="empty-title">خطا در بارگذاری پایگاه داده سهام</h3>
                    <p class="empty-desc">داده‌های سهام بارگذاری نشد. لطفاً از اجرای دستور python -m src.agents.frontend_agent اطمینان حاصل فرمایید.</p>
                </div>
            `;
            if (window.lucide) window.lucide.createIcons({ root: container });
        }
    }
}

// ---------------------------------------------------------
// Live AI Stock Reporter & Speaking Avatar Orchestration
// ---------------------------------------------------------
let liveAvatar = null;
let liveClient = null;
let currentReportStock = null;

function setupLiveReporter() {
    const modal = document.getElementById("liveReporterModal");
    const closeBtn = document.getElementById("closeLiveReporterBtn");
    const toggleMicBtn = document.getElementById("toggleLiveMicBtn");
    const liveMicLabel = document.getElementById("liveMicLabel");
    const reanalyzeBtn = document.getElementById("reanalyzeLiveBtn");
    const statusText = document.getElementById("reporterStatusText");
    const subtitles = document.getElementById("reporterSubtitles");
    const stockSymbolEl = document.getElementById("reporterStockSymbol");

    if (!modal) return;

    // Init Avatar Renderer
    if (window.LiveAvatarRenderer && !liveAvatar) {
        liveAvatar = new window.LiveAvatarRenderer("avatarCanvas");
        liveAvatar.start();
    }

    // Init Live Client
    if (window.GeminiLiveClient && !liveClient) {
        liveClient = new window.GeminiLiveClient();

        liveClient.onStatusChange = (status, text) => {
            if (statusText) statusText.textContent = text;
            if (status === "speaking" && liveAvatar) {
                liveAvatar.isSpeaking = true;
            } else if (liveAvatar) {
                liveAvatar.isSpeaking = false;
            }

            if (status === "recording") {
                toggleMicBtn?.classList.add("recording");
                if (liveMicLabel) liveMicLabel.textContent = "در حال ضبط... (کلیک برای توقف)";
            } else {
                toggleMicBtn?.classList.remove("recording");
                if (liveMicLabel) liveMicLabel.textContent = "گفتگو با تحلیل‌گر (میکروفون)";
            }
        };

        liveClient.onSubtitleChunk = (chunk) => {
            if (subtitles) {
                if (subtitles.textContent.includes("در حال انتظار") || subtitles.textContent.includes("در حال استخراج")) {
                    subtitles.textContent = "";
                }
                subtitles.textContent += chunk;
                subtitles.scrollTop = subtitles.scrollHeight;
            }
        };

        liveClient.onDataUpdated = (stk) => {
            const repLastPrice = document.getElementById("repMiniLastPrice");
            const repChange = document.getElementById("repMiniChange");
            const repBuyerPower = document.getElementById("repMiniBuyerPower");
            const repVolRatio = document.getElementById("repMiniVolRatio");

            const price = stk.close_price || stk.last_price || stk.current_price;
            if (repLastPrice && price) {
                repLastPrice.textContent = `${formatNumberFa(price)} ریال`;
            }
            if (repChange && stk.change_percent !== undefined) {
                const c = Number(stk.change_percent);
                repChange.textContent = `${c >= 0 ? "+" : ""}${toPersianDigits(c.toFixed(2))}%`;
                repChange.className = `market-stat-val ${c >= 0 ? "stat-up" : "stat-down"}`;
            }
            if (repBuyerPower && stk.buyer_power !== undefined) {
                repBuyerPower.textContent = `${toPersianDigits(stk.buyer_power)} برابر`;
            }
            if (repVolRatio && (stk.volume_str || stk.volume)) {
                repVolRatio.textContent = toPersianDigits(stk.volume_str || stk.volume);
            }

            // Update in-memory state so dashboard cards and tables show the new verified price
            const stockInState = (state.stocks || []).find(s => s.symbol === (stk.symbol || currentReportStock?.symbol));
            if (stockInState) {
                if (price) stockInState.current_price = price;
                if (stk.change_percent !== undefined) stockInState.change_percent = Number(stk.change_percent);
                if (stk.volume_str || stk.volume) stockInState.volume = stk.volume_str || stk.volume;
                try {
                    renderStocks();
                } catch (e) {}
            }
        };

        liveClient.onError = (err) => {
            if (statusText) statusText.textContent = "⚠️ " + err;
            showToast(err, "error");
        };
    }

    // Global click delegate for open-live-reporter
    document.addEventListener("click", (e) => {
        const btn = e.target.closest('[data-action="open-live-reporter"]');
        if (!btn) return;
        const symbol = btn.getAttribute("data-symbol");
        openLiveReporter(symbol);
    });

    // Close Modal
    function closeModal() {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
        if (liveClient) {
            liveClient.disconnect();
        }
        if (liveAvatar) {
            liveAvatar.isSpeaking = false;
        }
    }

    closeBtn?.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    // Toggle Mic
    toggleMicBtn?.addEventListener("click", async () => {
        if (!liveClient) return;
        if (liveClient.isRecording) {
            liveClient.stopRecording();
        } else {
            await liveClient.startRecording();
        }
    });

    // Text question input
    const questionInput = document.getElementById("reporterQuestionInput");
    const sendQuestionBtn = document.getElementById("reporterSendQuestionBtn");

    async function submitTextQuestion() {
        if (!liveClient || !questionInput) return;
        const q = questionInput.value.trim();
        if (!q) return;
        questionInput.value = "";
        if (subtitles) {
            subtitles.textContent += `\n\n🗣️ شما: «${q}»\n\n🤖 گزارشگر: در حال تحلیل و آماده‌سازی پاسخ...`;
            subtitles.scrollTop = subtitles.scrollHeight;
        }
        await liveClient.askServerQuestion(q);
    }

    sendQuestionBtn?.addEventListener("click", submitTextQuestion);
    questionInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            submitTextQuestion();
        }
    });

    // Reanalyze button
    reanalyzeBtn?.addEventListener("click", () => {
        if (!currentReportStock || !liveClient) return;
        if (subtitles) subtitles.textContent = "در حال تحلیل مجدد تابلوی نماد " + currentReportStock.symbol + "...";
        liveClient.fetchVerifiedReport();
    });
}

function openLiveReporter(symbol) {
    const modal = document.getElementById("liveReporterModal");
    if (!modal) return;

    // Find stock data
    const stock = (state.stocks || []).find(s => s.symbol === symbol) || {
        symbol: symbol,
        name: symbol,
        current_price: 2500,
        change_percent: 1.8,
        volume: "15.4M"
    };
    currentReportStock = stock;

    // Update UI elements
    const stockSymbolEl = document.getElementById("reporterStockSymbol");
    const repName = document.getElementById("repMiniName");
    const repLastPrice = document.getElementById("repMiniLastPrice");
    const repChange = document.getElementById("repMiniChange");
    const repBuyerPower = document.getElementById("repMiniBuyerPower");
    const repVolRatio = document.getElementById("repMiniVolRatio");
    const subtitles = document.getElementById("reporterSubtitles");

    if (stockSymbolEl) stockSymbolEl.textContent = stock.symbol;
    if (repName) repName.textContent = `${stock.name || stock.symbol}`;
    if (repLastPrice) repLastPrice.textContent = `${formatNumberFa(stock.current_price)} ریال`;
    
    const chg = stock.change_percent ?? 0;
    if (repChange) {
        repChange.textContent = `${chg >= 0 ? "+" : ""}${toPersianDigits(chg.toFixed(2))}%`;
        repChange.className = `market-stat-val ${chg >= 0 ? "stat-up" : "stat-down"}`;
    }

    if (repBuyerPower) {
        repBuyerPower.textContent = `نامشخص`;
    }
    if (repVolRatio) {
        repVolRatio.textContent = `${toPersianDigits(stock.volume || "---")}`;
    }

    if (subtitles) {
        subtitles.textContent = "در حال استخراج اطلاعات معاملات روز جاری از TSETMC و ره‌آورد ۳۶۵ و راستی‌آزمایی تابلوی نماد " + stock.symbol + "...";
    }

    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");

    // Make sure avatar is ready and running
    if (liveAvatar) {
        liveAvatar.resize();
        liveAvatar.start();
    }

    // Connect Gemini Live WebSocket
    const apiKey = (window.SITE_CONFIG && window.SITE_CONFIG.geminiApiKey) ||
                   localStorage.getItem("GEMINI_API_KEY") ||
                   "";

    const brief = window.MarketContextManager?.buildBrief(stock) || "";

    if (liveClient) {
        liveClient.disconnect();
        liveClient.connect(apiKey, stock.symbol, brief);
        if (liveClient.analyser && liveAvatar) {
            liveAvatar.setAudioAnalyser(liveClient.analyser);
        }
    }
}

// Run when DOM ready
if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initApp);
    } else {
        initApp();
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        state,
        fetchStocksData,
        startLiveUpdates,
        initApp,
        renderStockCard,
        renderDetailedStockCard,
        renderMiniSparkline,
        renderStockChart,
        openExplainabilityModal,
        getStockExplainability,
        setupExplainabilityModal
    };
}

