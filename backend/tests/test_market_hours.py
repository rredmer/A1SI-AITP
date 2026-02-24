"""Tests for MarketHoursService — market open/close detection for all asset classes."""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.market_hours.sessions import MarketHoursService

ET = ZoneInfo("America/New_York")


def _et(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> datetime:
    """Create a timezone-aware datetime in US/Eastern."""
    return datetime(year, month, day, hour, minute, tzinfo=ET)


class TestCryptoAlwaysOpen:
    def test_crypto_is_open_returns_true(self):
        assert MarketHoursService.is_market_open("crypto") is True

    def test_crypto_next_open_returns_none(self):
        assert MarketHoursService.next_open("crypto") is None

    def test_crypto_next_close_returns_none(self):
        assert MarketHoursService.next_close("crypto") is None

    def test_crypto_session_info_structure(self):
        info = MarketHoursService.get_session_info("crypto")
        assert info["is_open"] is True
        assert info["session"] == "crypto_24_7"
        assert info["next_open"] is None
        assert info["next_close"] is None


class TestEquityMarketHours:
    def test_open_during_regular_hours(self):
        # Wed 12:00 PM ET
        now = _et(2026, 2, 25, 12, 0)
        assert MarketHoursService.is_market_open("equity", now) is True

    def test_closed_before_open(self):
        # Wed 9:00 AM ET — before 9:30
        now = _et(2026, 2, 25, 9, 0)
        assert MarketHoursService.is_market_open("equity", now) is False

    def test_closed_after_close(self):
        # Wed 4:01 PM ET — after 4:00
        now = _et(2026, 2, 25, 16, 1)
        assert MarketHoursService.is_market_open("equity", now) is False

    def test_closed_on_saturday(self):
        # Sat Feb 28 2026
        now = _et(2026, 2, 28, 12, 0)
        assert MarketHoursService.is_market_open("equity", now) is False

    def test_closed_on_sunday(self):
        # Sun Mar 1 2026
        now = _et(2026, 3, 1, 12, 0)
        assert MarketHoursService.is_market_open("equity", now) is False

    def test_closed_on_holiday_new_year_2026(self):
        # Jan 1 2026 (Thu) — US holiday
        now = _et(2026, 1, 1, 12, 0)
        assert MarketHoursService.is_market_open("equity", now) is False

    def test_open_at_930_exactly(self):
        # Wed 9:30 AM ET — boundary: >= 9:30 is open
        now = _et(2026, 2, 25, 9, 30)
        assert MarketHoursService.is_market_open("equity", now) is True

    def test_closed_at_1600_exactly(self):
        # Wed 4:00 PM ET — boundary: < 16:00 is open, so at 16:00 it's closed
        now = _et(2026, 2, 25, 16, 0)
        assert MarketHoursService.is_market_open("equity", now) is False


class TestEquityNextOpen:
    def test_returns_none_when_already_open(self):
        # Wed 12:00 PM ET — market is open
        now = _et(2026, 2, 25, 12, 0)
        assert MarketHoursService.next_open("equity", now) is None

    def test_after_close_returns_next_day(self):
        # Wed 5:00 PM ET — after close, next open is Thu 9:30 AM ET
        now = _et(2026, 2, 25, 17, 0)
        result = MarketHoursService.next_open("equity", now)
        assert result is not None
        result_et = result.astimezone(ET)
        assert result_et.weekday() == 3  # Thursday
        assert result_et.hour == 9
        assert result_et.minute == 30

    def test_skips_weekend(self):
        # Fri 5:00 PM ET — next open should be Mon 9:30 AM ET
        now = _et(2026, 2, 27, 17, 0)
        result = MarketHoursService.next_open("equity", now)
        assert result is not None
        result_et = result.astimezone(ET)
        assert result_et.weekday() == 0  # Monday
        assert result_et.hour == 9
        assert result_et.minute == 30


class TestForexMarketHours:
    def test_open_on_tuesday(self):
        # Tue 12:00 PM ET — forex always open Mon-Thu
        now = _et(2026, 2, 24, 12, 0)
        assert MarketHoursService.is_market_open("forex", now) is True

    def test_closed_on_saturday(self):
        # Sat Feb 28 2026
        now = _et(2026, 2, 28, 12, 0)
        assert MarketHoursService.is_market_open("forex", now) is False

    def test_open_sunday_after_5pm_et(self):
        # Sun 5:01 PM ET — forex opens at 5PM Sunday
        now = _et(2026, 3, 1, 17, 1)
        assert MarketHoursService.is_market_open("forex", now) is True

    def test_closed_sunday_before_5pm_et(self):
        # Sun 4:59 PM ET — before forex opens
        now = _et(2026, 3, 1, 16, 59)
        assert MarketHoursService.is_market_open("forex", now) is False


class TestGetSessionInfo:
    def test_session_info_keys_present(self):
        info = MarketHoursService.get_session_info("equity", _et(2026, 2, 25, 12, 0))
        assert set(info.keys()) == {"is_open", "session", "timezone", "next_open", "next_close"}

    def test_next_open_iso_format_when_closed(self):
        # Sat — market closed, next_open should be an ISO string
        info = MarketHoursService.get_session_info("equity", _et(2026, 2, 28, 12, 0))
        assert info["is_open"] is False
        assert info["next_open"] is not None
        assert isinstance(info["next_open"], str)
        assert "T" in info["next_open"]  # ISO format
