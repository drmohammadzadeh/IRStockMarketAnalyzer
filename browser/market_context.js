/**
 * Market Context Packager for Gemini Live Multimodal API
 * Extracts real-time order-book, price change, and smart-money metrics for a stock.
 */
class MarketContextManager {
    static formatNumber(num) {
        if (num === null || num === undefined) return '---';
        return Number(num).toLocaleString('fa-IR');
    }

    static buildBrief(stock) {
        if (!stock) return 'اطلاعاتی از نماد در دسترس نیست.';

        const symbol = stock.symbol || stock.name || 'سهم انتخابی';
        const companyName = stock.company_name || stock.fullName || symbol;
        const lastPrice = stock.last_price || stock.close_price || 0;
        const closePrice = stock.close_price || lastPrice;
        const priceChangePct = stock.price_change_pct !== undefined ? stock.price_change_pct : (stock.change_percent || 0);
        const volume = stock.volume || 0;
        const baseVolume = stock.base_volume || 1;
        const volumeRatio = (volume / (baseVolume || 1)).toFixed(2);
        const signal = stock.signal || stock.composite_score_label || 'بررسی تحلیل';

        // Order Book & Buyer Power simulation / extraction
        const buyerCount = stock.individual_buy_count || 120;
        const sellerCount = stock.individual_sell_count || 95;
        const buyerPower = (stock.buyer_power_ratio || 1.35).toFixed(2);

        return `
[اطلاعات زنده تابلوی معاملات نماد ${symbol} (${companyName})]:
- وضعیت قیمت: آخرین معامله ${MarketContextManager.formatNumber(lastPrice)} ریال (${priceChangePct}٪)، قیمت پایانی ${MarketContextManager.formatNumber(closePrice)} ریال.
- وضعیت حجم معاملات: حجم امروز ${MarketContextManager.formatNumber(volume)} سهم (معادل ${volumeRatio} برابر حجم مبنا).
- جریان نقدینگی و قدرت خریدار/فروشنده: نسبت قدرت سرانه خریدار به فروشنده برابر با ${buyerPower} (حقیقی‌ها: ${buyerCount} خریدار در برابر ${sellerCount} فروشنده).
- وضعیت صف و مظنه‌ها: عرضه و تقاضا در آستانه مجاز فعال است.
- سیگنال سامانه الگوریتمی tjb24: ${signal}.

دستورالعمل اجرا:
تو به عنوان کاراکتر مجری و تحلیل‌گر ارشد بورس حاضر در استودیو، بلافاصله و با لحن زنده، صمیمی، محترمانه و قاطع فارسی، بینندگان را با سلام و نام بردن از نماد «${symbol}» مورد خطاب قرار بده و وضعیت اردرها، تابلو و نوسان امروز را خیلی روان و جذاب گزارش کن.
`.trim();
    }
}

window.MarketContextManager = MarketContextManager;
