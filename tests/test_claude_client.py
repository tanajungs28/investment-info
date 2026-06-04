from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from reporters.claude_client import generate_summary, SummaryResult
from collectors.news import NewsItem
from collectors.market import PriceData


def make_news_items() -> list[NewsItem]:
    return [
        NewsItem(
            title="NVIDIAが新型GPU発表",
            url="http://example.com",
            source="株探",
            published=datetime.now(timezone.utc),
            tickers=["NVDA"],
        )
    ]


def make_market_data() -> dict:
    return {
        "us_stocks": [PriceData("NVDA", "NVIDIA", 900.0, 3.5)],
        "jp_stocks": [],
    }


@patch("reporters.claude_client.anthropic.Anthropic")
def test_generate_summary_returns_summary_result(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="① ポイント1\n② ポイント2\n③ ポイント3")]
    mock_client.messages.create.return_value = mock_response

    result = generate_summary(make_news_items(), make_market_data(), api_key="test-key")
    assert isinstance(result, SummaryResult)
    assert len(result.key_points) >= 1


@patch("reporters.claude_client.anthropic.Anthropic")
def test_generate_summary_returns_none_on_api_error(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API error")

    result = generate_summary([], {}, api_key="test-key")
    assert result is None
