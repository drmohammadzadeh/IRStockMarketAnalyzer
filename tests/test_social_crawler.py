# Author: alimohammadzadeh@ut.ac.ir
"""Tests for SocialSentimentCrawler covering Sahamyab, Rahavard365, and Sentiment Analysis."""

import json
from pathlib import Path
import pytest
import httpx
from unittest.mock import MagicMock, patch

from src.data.social_crawler import SocialSentimentCrawler


def test_social_crawler_initialization():
    """Verify crawler initializes properly with default and custom client."""
    crawler = SocialSentimentCrawler()
    assert crawler.client is not None

    custom_client = httpx.Client()
    crawler_custom = SocialSentimentCrawler(client=custom_client)
    assert crawler_custom.client is custom_client


def test_analyze_sentiment_empty():
    """Verify sentiment analysis on empty comments list returns neutral 5.0 score."""
    crawler = SocialSentimentCrawler()
    res = crawler.analyze_sentiment([])
    assert res["bullish_count"] == 0
    assert res["bearish_count"] == 0
    assert res["neutral_count"] == 0
    assert res["composite_sentiment_score"] == 5.0
    assert "خنثی" in res["sentiment_verdict"]


def test_analyze_sentiment_bullish():
    """Verify bullish keywords increase sentiment score towards 10.0."""
    crawler = SocialSentimentCrawler()
    comments = [
        "سهم فردا صف خرید سنگین خواهد داشت و هدف رشد ۵۰ درصدی دارد",
        "ورود پول هوشمند دیده شد و سهم بسیار ارزنده است",
        "حمایت معتبر حفظ شد و حرکت شارپ صعودی در پیش داریم",
        "تارگت اول تاچ شد، سود عالی برای سهامداران صبور",
    ]
    res = crawler.analyze_sentiment(comments)
    assert res["bullish_count"] >= 3
    assert res["bearish_count"] == 0
    assert res["composite_sentiment_score"] > 7.0
    assert "صعودی" in res["sentiment_verdict"] or "مثبت" in res["sentiment_verdict"]


def test_analyze_sentiment_bearish():
    """Verify bearish keywords decrease sentiment score towards 0.0."""
    crawler = SocialSentimentCrawler()
    comments = [
        "فردا صف فروش سنگین و قفل در صف",
        "خروج پول حقیقی و ریزش شدید تا کف بعدی",
        "سهم حباب کامل است و خطر زیان بالا وجود دارد",
        "مقاومت مهم رد نشد و سهم نزول و افت قیمت خواهد داشت",
    ]
    res = crawler.analyze_sentiment(comments)
    assert res["bearish_count"] >= 3
    assert res["bullish_count"] == 0
    assert res["composite_sentiment_score"] < 3.0
    assert "نزولی" in res["sentiment_verdict"] or "منفی" in res["sentiment_verdict"]


def test_analyze_sentiment_mixed():
    """Verify mixed comments compute balanced score within 0.0 - 10.0."""
    crawler = SocialSentimentCrawler()
    comments = [
        "رشد سهم تا تارگت قطعی است",
        "صف فروش و ریزش سنگین در راه است",
        "معاملات عادی و در محدوده رنج",
    ]
    res = crawler.analyze_sentiment(comments)
    assert res["bullish_count"] == 1
    assert res["bearish_count"] == 1
    assert res["neutral_count"] == 1
    assert 4.0 <= res["composite_sentiment_score"] <= 6.0


def test_fetch_sahamyab_comments_mocked():
    """Verify parsing Sahamyab API response."""
    crawler = SocialSentimentCrawler()
    mock_payload = {
        "items": [
            {
                "id": "1001",
                "content": "نماد #فولاد بسیار ارزنده است و آماده صف خرید",
                "senderName": "علی رضایی",
                "senderUsername": "ali_reza",
                "sendTime": "2026-09-02T12:00:00",
                "likeCount": 15,
            },
            {
                "id": "1002",
                "content": "ریزش شاخص کل و افت قیمت",
                "senderName": "تحلیلگر بازار",
                "senderUsername": "market_pro",
                "sendTime": "2026-09-02T12:05:00",
                "likeCount": 3,
            },
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status = MagicMock()

    with patch.object(crawler.client, "get", return_value=mock_response):
        comments = crawler.fetch_sahamyab_comments("فولاد")
        assert len(comments) == 2
        assert comments[0]["author"] == "علی رضایی"
        assert "ارزنده" in comments[0]["content"]
        assert comments[0]["likes"] == 15
        assert comments[0]["source"] == "sahamyab"


def test_fetch_sahamyab_comments_fallback_on_network_error():
    """Verify fallback handling when Sahamyab network request fails."""
    crawler = SocialSentimentCrawler()
    with patch.object(crawler.client, "get", side_effect=httpx.ConnectError("Network unreachable")):
        comments = crawler.fetch_sahamyab_comments("فولاد")
        assert isinstance(comments, list)


def test_fetch_rahavard_comments_mocked():
    """Verify parsing Rahavard365 API/discussion response."""
    crawler = SocialSentimentCrawler()
    mock_payload = {
        "data": [
            {
                "body": "تحلیل تکنیکال: حمایت خط روند حفظ شد و انتظار رشد داریم.",
                "user": {"name": "سرمایه‌گذار"},
                "created_at": "1405-06-11 10:00",
                "votes_count": 8,
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status = MagicMock()

    with patch.object(crawler.client, "get", return_value=mock_response):
        comments = crawler.fetch_rahavard_comments("فولاد")
        assert len(comments) >= 1
        assert "حمایت" in comments[0]["content"]
        assert comments[0]["source"] == "rahavard365"


def test_fetch_rahavard_comments_fallback_on_network_error():
    """Verify fallback handling when Rahavard365 network request fails."""
    crawler = SocialSentimentCrawler()
    with patch.object(crawler.client, "get", side_effect=httpx.TimeoutException("Timeout")):
        comments = crawler.fetch_rahavard_comments("فولاد")
        assert isinstance(comments, list)


def test_crawl_and_save_structure(tmp_path):
    """Verify crawl_and_save creates news/social_sentiment.json with all required keys."""
    crawler = SocialSentimentCrawler()
    
    crawler.fetch_sahamyab_comments = MagicMock(return_value=[
        {"content": "سهم صف خرید سنگین و رشد شارپ خواهد داشت", "author": "کاربر ۱", "created_at": "1405-06-11", "likes": 10, "source": "sahamyab"},
        {"content": "ارزنده و ورود پول عالی", "author": "کاربر ۲", "created_at": "1405-06-11", "likes": 5, "source": "sahamyab"},
    ])
    crawler.fetch_rahavard_comments = MagicMock(return_value=[
        {"content": "تحلیل تکنیکال صعودی و تارگت بالا", "author": "کاربر ۳", "created_at": "1405-06-11", "likes": 7, "source": "rahavard365"},
    ])

    res = crawler.crawl_and_save("فولاد", tmp_path)
    assert res["success"] is True
    assert res["symbol"] == "فولاد"
    out_file = tmp_path / "news" / "social_sentiment.json"
    assert out_file.exists()
    assert res["file_path"] == str(out_file)

    saved_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert saved_data["symbol"] == "فولاد"
    assert "fetch_timestamp" in saved_data
    assert "sahamyab" in saved_data
    assert saved_data["sahamyab"]["total_posts"] == 2
    assert saved_data["sahamyab"]["bullish_count"] == 2
    assert "rahavard365" in saved_data
    assert saved_data["rahavard365"]["total_posts"] == 1
    assert saved_data["rahavard365"]["bullish_count"] == 1
    assert "composite_sentiment_score" in saved_data
    assert 0.0 <= saved_data["composite_sentiment_score"] <= 10.0
    assert saved_data["composite_sentiment_score"] >= 8.0
    assert "sentiment_verdict" in saved_data
