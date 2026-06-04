from unittest.mock import patch, MagicMock
import time as time_mod
from collectors.calendar import parse_forex_factory_events, EconomicEvent


def make_entry(title: str, description: str) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.get = lambda key, default="": description if key == "description" else default
    entry.published_parsed = time_mod.strptime("Wed, 04 Jun 2025 13:30:00", "%a, %d %b %Y %H:%M:%S")
    return entry


@patch("collectors.calendar.feedparser.parse")
def test_parse_returns_high_importance_events(mock_parse):
    mock_parse.return_value.entries = [
        make_entry("CPI (MoM)", "High|USD|CPI|0.3%|0.2%"),
        make_entry("Minor Data", "Low|USD|Minor||"),
    ]
    events = parse_forex_factory_events("http://example.com/rss", min_importance=2)
    assert len(events) == 1
    assert events[0].title == "CPI (MoM)"
    assert events[0].importance == 3


@patch("collectors.calendar.feedparser.parse")
def test_parse_returns_empty_list_on_error(mock_parse):
    mock_parse.side_effect = Exception("Network error")
    events = parse_forex_factory_events("http://example.com/rss")
    assert events == []


def test_economic_event_dataclass():
    event = EconomicEvent(time="22:30", currency="USD", title="FOMC", importance=3)
    assert event.currency == "USD"
    assert event.importance == 3
