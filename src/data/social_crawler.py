# Author: alimohammadzadeh@ut.ac.ir
"""Social Sentiment Crawler for Sahamyab and Rahavard365."""

import json
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

from src.config import HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class SocialSentimentCrawler:
    """Extracts and analyzes social chatter and sentiment for Iranian stock market symbols."""

    BULLISH_KEYWORDS = [
        "صف خرید",
        "رشد",
        "شارپ",
        "صعود",
        "حمایت",
        "ارزنده",
        "ورود پول",
        "مثبت",
        "تارگت",
        "سود",
        "عالی",
        "ارزندگی",
        "خرید",
        "پرواز",
        "صعودی",
        "شکست مقاومت",
    ]

    BEARISH_KEYWORDS = [
        "صف فروش",
        "ریزش",
        "افت",
        "نزول",
        "مقاومت",
        "خروج پول",
        "منفی",
        "زیان",
        "حباب",
        "خطر",
        "ریسک",
        "خالی کردند",
        "فروش",
        "نزولی",
        "شکست حمایت",
    ]

    def __init__(
        self,
        client: Optional[httpx.Client] = None,
        timeout: int = REQUEST_TIMEOUT,
    ):
        """Initializes the social crawler with an HTTP client."""
        self.client = client or httpx.Client(
            headers=HEADERS,
            timeout=timeout,
            verify=False,
            follow_redirects=True,
            trust_env=False,
        )

    def fetch_sahamyab_comments(self, symbol: str) -> List[Dict[str, Any]]:
        """Queries Sahamyab public hashtag stream to extract user comments.
        
        Endpoint: https://www.sahamyab.com/guest/twiter/list?v=0.1&hashtag={symbol}&page=0
        """
        encoded_symbol = urllib.parse.quote(symbol)
        url = f"https://www.sahamyab.com/guest/twiter/list?v=0.1&hashtag={encoded_symbol}&page=0"
        headers = {
            **HEADERS,
            "Referer": f"https://www.sahamyab.com/hashtag/{encoded_symbol}",
            "Accept": "application/json, text/plain, */*",
        }

        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            raw_items = []
            if isinstance(data, dict):
                raw_items = data.get("items") or data.get("data") or data.get("list") or []
            elif isinstance(data, list):
                raw_items = data

            comments: List[Dict[str, Any]] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                content = (
                    item.get("content")
                    or item.get("body")
                    or item.get("text")
                    or ""
                ).strip()
                if not content:
                    continue
                author = (
                    item.get("senderName")
                    or item.get("senderUsername")
                    or item.get("author")
                    or "کاربر سهام‌یاب"
                )
                created_at = (
                    item.get("sendTimePersian")
                    or item.get("sendTime")
                    or item.get("created_at")
                    or ""
                )
                likes = int(item.get("likeCount") or item.get("likes") or 0)
                comments.append({
                    "content": content,
                    "author": author,
                    "created_at": str(created_at),
                    "likes": likes,
                    "source": "sahamyab",
                })
            return comments

        except Exception as exc:
            logger.warning("Failed to fetch Sahamyab comments for symbol %s: %s", symbol, exc)
            return []

    def fetch_rahavard_comments(self, symbol: str) -> List[Dict[str, Any]]:
        """Queries Rahavard365 asset discussions and ideas for the symbol."""
        encoded_symbol = urllib.parse.quote(symbol)
        url = f"https://rahavard365.com/api/posts?slug={encoded_symbol}"
        headers = {
            **HEADERS,
            "Referer": f"https://rahavard365.com/asset/{encoded_symbol}",
            "Accept": "application/json, text/plain, */*",
        }

        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            raw_items = []
            if isinstance(data, dict):
                raw_items = data.get("data") or data.get("items") or data.get("posts") or []
            elif isinstance(data, list):
                raw_items = data

            comments: List[Dict[str, Any]] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                content = (
                    item.get("body")
                    or item.get("content")
                    or item.get("text")
                    or ""
                ).strip()
                if not content:
                    continue
                user_info = item.get("user") or {}
                if isinstance(user_info, dict):
                    author = user_info.get("name") or user_info.get("username") or "کاربر ره‌آورد"
                else:
                    author = str(user_info)
                created_at = item.get("created_at") or item.get("date") or ""
                likes = int(item.get("votes_count") or item.get("likes") or item.get("vote") or 0)
                comments.append({
                    "content": content,
                    "author": author,
                    "created_at": str(created_at),
                    "likes": likes,
                    "source": "rahavard365",
                })
            return comments

        except Exception as exc:
            logger.warning("Failed to fetch Rahavard365 comments for symbol %s: %s", symbol, exc)
            return []

    def analyze_sentiment(
        self,
        comments: List[Union[str, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Categorizes comments using Persian financial keywords and computes composite sentiment score."""
        total_posts = len(comments)
        if total_posts == 0:
            return {
                "total_posts": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "composite_sentiment_score": 5.0,
                "sentiment_verdict": "خنثی / بدون جهت‌گیری خاص",
                "sample_comments": [],
            }

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        sample_texts: List[str] = []

        for item in comments:
            text = item.get("content", "") if isinstance(item, dict) else str(item)
            text_clean = text.strip()
            if not text_clean:
                neutral_count += 1
                continue

            if len(sample_texts) < 5:
                sample_texts.append(text_clean)

            bullish_hits = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text_clean)
            bearish_hits = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text_clean)

            if bullish_hits > bearish_hits:
                bullish_count += 1
            elif bearish_hits > bullish_hits:
                bearish_count += 1
            else:
                neutral_count += 1

        # Composite sentiment calculation normalized from 0.0 to 10.0
        net_ratio = (bullish_count - bearish_count) / total_posts
        score = round(max(0.0, min(10.0, 5.0 + (net_ratio * 5.0))), 2)

        if score >= 7.5:
            verdict = "خوش‌بینی بالا در میان سهامداران خرد و فعالان شبکه‌های اجتماعی (جو بسیار صعودی)"
        elif score >= 6.0:
            verdict = "دیدگاه مثبت و تمایل به خرید در شبکه‌های اجتماعی (جو صعودی)"
        elif score >= 4.0:
            verdict = "جو خنثی و بدون جهت‌گیری مشخص در میان فعالان بازار"
        elif score >= 2.5:
            verdict = "دیدگاه منفی و احتیاط در شبکه‌های اجتماعی (جو نزولی)"
        else:
            verdict = "بدبینی شدید و فشار فروش در شبکه‌های اجتماعی (جو بسیار نزولی)"

        return {
            "total_posts": total_posts,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "composite_sentiment_score": score,
            "sentiment_verdict": verdict,
            "sample_comments": sample_texts,
        }

    def crawl_and_save(
        self,
        symbol: str,
        symbol_dir: Union[str, Path],
    ) -> Dict[str, Any]:
        """Fetches comments from Sahamyab and Rahavard365, analyzes sentiment, and writes news/social_sentiment.json."""
        target_dir = Path(symbol_dir)
        news_dir = target_dir / "news"
        news_dir.mkdir(parents=True, exist_ok=True)

        sahamyab_posts = self.fetch_sahamyab_comments(symbol)
        rahavard_posts = self.fetch_rahavard_comments(symbol)

        sahamyab_analysis = self.analyze_sentiment(sahamyab_posts)
        rahavard_analysis = self.analyze_sentiment(rahavard_posts)

        all_posts = sahamyab_posts + rahavard_posts
        combined_analysis = self.analyze_sentiment(all_posts)

        payload = {
            "symbol": symbol,
            "fetch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sahamyab": {
                "total_posts": sahamyab_analysis["total_posts"],
                "bullish_count": sahamyab_analysis["bullish_count"],
                "bearish_count": sahamyab_analysis["bearish_count"],
                "neutral_count": sahamyab_analysis["neutral_count"],
                "sample_comments": [
                    p.get("content", str(p)) if isinstance(p, dict) else str(p)
                    for p in sahamyab_posts[:5]
                ],
            },
            "rahavard365": {
                "total_posts": rahavard_analysis["total_posts"],
                "bullish_count": rahavard_analysis["bullish_count"],
                "bearish_count": rahavard_analysis["bearish_count"],
                "neutral_count": rahavard_analysis["neutral_count"],
                "sample_comments": [
                    p.get("content", str(p)) if isinstance(p, dict) else str(p)
                    for p in rahavard_posts[:5]
                ],
            },
            "composite_sentiment_score": combined_analysis["composite_sentiment_score"],
            "sentiment_verdict": combined_analysis["sentiment_verdict"],
        }

        out_file = news_dir / "social_sentiment.json"
        out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "success": True,
            "symbol": symbol,
            "data": payload,
            "file_path": str(out_file),
        }
