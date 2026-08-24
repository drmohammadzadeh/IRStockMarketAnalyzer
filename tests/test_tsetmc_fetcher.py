import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.data.tsetmc_fetcher import TSETMCFetcher


def test_parse_history_data():
    raw_history = (
        "20260220@4600@4480@4520@4500@4500@4480@5424000000@1200000@150;"
        "20260221@4650@4510@4620@4600@4520@4520@6930000000@1500000@200;"
    )
    df = TSETMCFetcher.parse_history_string(raw_history)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "close" in df.columns
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "volume" in df.columns
    assert df.iloc[-1]["close"] == 4620.0
    assert df.iloc[-1]["open"] == 4520.0
    assert df.iloc[-1]["high"] == 4650.0
    assert df.iloc[-1]["low"] == 4510.0
    assert df.iloc[-1]["volume"] == 1500000.0
    assert df.iloc[-1]["value"] == 6930000000.0
    assert df.iloc[-1]["trades"] == 200.0


def test_parse_history_data_empty_or_invalid():
    df_empty = TSETMCFetcher.parse_history_string("")
    assert isinstance(df_empty, pd.DataFrame)
    assert df_empty.empty

    df_invalid = TSETMCFetcher.parse_history_string("invalid@data;another@invalid")
    assert isinstance(df_invalid, pd.DataFrame)
    assert df_invalid.empty


def test_parse_client_type():
    # Format: Date, BuyRealCount, BuyLegalCount, SellRealCount, SellLegalCount, BuyRealVol, BuyLegalVol, SellRealVol, SellLegalVol
    raw_client = "20260221,120,5,50,1,1000000,100000,500000,200000;"
    result = TSETMCFetcher.parse_client_type_string(raw_client)
    assert result["buy_real_count"] == 120
    assert result["buy_legal_count"] == 5
    assert result["sell_real_count"] == 50
    assert result["sell_legal_count"] == 1
    assert result["buy_real_vol"] == 1000000.0
    assert result["buy_legal_vol"] == 100000.0
    assert result["sell_real_vol"] == 500000.0
    assert result["sell_legal_vol"] == 200000.0
    assert result["buy_real_capita"] == 1000000.0 / 120
    assert result["sell_real_capita"] == 500000.0 / 50
    assert result["buyer_power"] == (1000000.0 / 120) / (500000.0 / 50)


def test_parse_client_type_empty_or_invalid():
    res_empty = TSETMCFetcher.parse_client_type_string("")
    assert res_empty == {}

    res_invalid = TSETMCFetcher.parse_client_type_string("not,enough,data")
    assert res_invalid == {}


def test_search_inscode():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "زهلال,12345678901234567,شیر پگاه لرستان;فولاد,98765432109876543,فولاد مبارکه اصفهان;"
    mock_client.get.return_value = mock_resp

    fetcher = TSETMCFetcher(client=mock_client)
    inscode = fetcher.search_inscode("زهلال")
    assert inscode == "12345678901234567"


def test_search_inscode_not_found():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "فولاد,98765432109876543,فولاد مبارکه اصفهان;"
    mock_client.get.return_value = mock_resp

    fetcher = TSETMCFetcher(client=mock_client)
    inscode = fetcher.search_inscode("زهلال")
    assert inscode is None


def test_fetch_symbol_data_success():
    mock_client = MagicMock()

    def mock_get(url):
        resp = MagicMock()
        resp.status_code = 200
        if "search.aspx" in url:
            resp.text = "زهلال,12345678901234567,شیر پگاه لرستان;"
        elif "InstTradeHistory.aspx" in url:
            resp.text = "20260220@4600@4480@4520@4500@4500@4480@5424000000@1200000@150;"
        elif "clienttype.aspx" in url:
            resp.text = "20260220,100,2,50,1,500000,10000,250000,20000;"
        else:
            resp.status_code = 404
            resp.text = ""
        return resp

    mock_client.get.side_effect = mock_get

    fetcher = TSETMCFetcher(client=mock_client)
    data = fetcher.fetch_symbol_data("زهلال")

    assert data["success"] is True
    assert data["symbol"] == "زهلال"
    assert data["inscode"] == "12345678901234567"
    assert isinstance(data["history"], pd.DataFrame)
    assert len(data["history"]) == 1
    assert data["client_type"]["buy_real_count"] == 100


def test_fetch_symbol_data_not_found():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = ""
    mock_client.get.return_value = mock_resp

    fetcher = TSETMCFetcher(client=mock_client)
    data = fetcher.fetch_symbol_data("ناموجود")

    assert data["success"] is False
    assert "error" in data
