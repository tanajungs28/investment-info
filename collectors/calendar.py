from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import feedparser

logger = logging.getLogger(__name__)

IMPORTANCE_MAP = {"High": 3, "Medium": 2, "Low": 1}


@dataclass
class EconomicEvent:
    time: str
    currency: str
    title: str
    importance: int


def parse_forex_factory_events(
    url: str, min_importance: int = 2
) -> list[EconomicEvent]:
    try:
        feed = feedparser.parse(url)
        events = []
        for entry in feed.entries:
            description = entry.get("description", "")
            parts = description.split("|")
            if len(parts) < 2:
                continue
            importance_str = parts[0].strip()
            currency = parts[1].strip()
            importance = IMPORTANCE_MAP.get(importance_str, 0)
            if importance < min_importance:
                continue
            try:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                time_str = published.strftime("%H:%M")
            except Exception:
                time_str = "??:??"
            events.append(
                EconomicEvent(
                    time=time_str,
                    currency=currency,
                    title=entry.title,
                    importance=importance,
                )
            )
        return events
    except Exception as e:
        logger.warning("Failed to fetch economic calendar: %s", e)
        return []
