"""Tests for tdnet-disclosure-mcp models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from tdnet_disclosure_mcp.models import (
    Disclosure,
    DisclosureCategory,
    DisclosureList,
    _categorize,
)


class TestDisclosureCategory:
    """Test disclosure category detection."""

    def test_earnings(self) -> None:
        assert _categorize("2024年3月期 決算短信〔日本基準〕") == DisclosureCategory.EARNINGS

    def test_dividend(self) -> None:
        assert _categorize("配当予想の修正に関するお知らせ") == DisclosureCategory.DIVIDEND

    def test_forecast_revision(self) -> None:
        result = _categorize("業績予想の修正に関するお知らせ")
        assert result == DisclosureCategory.FORECAST_REVISION

    def test_buyback(self) -> None:
        assert _categorize("自己株式の取得に係る事項の決定") == DisclosureCategory.BUYBACK

    def test_offering(self) -> None:
        assert _categorize("新株予約権の発行に関するお知らせ") == DisclosureCategory.OFFERING

    def test_governance(self) -> None:
        assert _categorize("代表取締役の異動に関するお知らせ") == DisclosureCategory.GOVERNANCE

    def test_other(self) -> None:
        assert _categorize("定款の一部変更に関するお知らせ") == DisclosureCategory.OTHER

    def test_quarterly_report(self) -> None:
        assert _categorize("四半期報告書") == DisclosureCategory.EARNINGS

    def test_self_stock(self) -> None:
        assert _categorize("自社株買いに関するお知らせ") == DisclosureCategory.BUYBACK


class TestDisclosure:
    """Test Disclosure model."""

    def test_create_valid(self) -> None:
        d = Disclosure(
            id="12345",
            pubdate=datetime(2026, 2, 14, 15, 30),
            company_code="7203",
            company_name="トヨタ自動車",
            title="決算短信",
            category=DisclosureCategory.EARNINGS,
        )

        assert d.company_code == "7203"
        assert d.company_name == "トヨタ自動車"
        assert d.category == DisclosureCategory.EARNINGS

    def test_invalid_code(self) -> None:
        with pytest.raises(ValidationError):
            Disclosure(
                id="12345",
                pubdate=datetime(2026, 2, 14),
                company_code="ABC",
                company_name="Test",
                title="Test",
            )

    def test_frozen(self) -> None:
        d = Disclosure(
            id="12345",
            pubdate=datetime(2026, 2, 14),
            company_code="7203",
            company_name="Test",
            title="Test",
        )
        with pytest.raises(ValidationError):
            d.title = "Changed"

    def test_from_api(self) -> None:
        item = {
            "Tdnet": {
                "id": "12345",
                "pubdate": "2026-02-14 15:30:00",
                "company_code": "72030",
                "company_name": "トヨタ自動車  ",
                "title": "2025年3月期 決算短信〔日本基準〕",
                "document_url": "https://example.com/doc.pdf",
                "url_xbrl": None,
                "markets_string": "東",
                "update_history": None,
            }
        }

        d = Disclosure.from_api(item)

        assert d.id == "12345"
        assert d.company_code == "7203"
        assert d.company_name == "トヨタ自動車"
        assert d.category == DisclosureCategory.EARNINGS
        assert d.exchange == "東"

    def test_from_api_4digit_code(self) -> None:
        item = {
            "Tdnet": {
                "id": "99",
                "pubdate": "2026-01-01 09:00:00",
                "company_code": "6758",
                "company_name": "ソニー",
                "title": "お知らせ",
            }
        }

        d = Disclosure.from_api(item)
        assert d.company_code == "6758"


class TestDisclosureList:
    """Test DisclosureList model."""

    def test_create_empty(self) -> None:
        result = DisclosureList()

        assert result.total_count == 0
        assert result.disclosures == []

    def test_to_dict(self) -> None:
        d = Disclosure(
            id="1",
            pubdate=datetime(2026, 2, 14, 15, 0),
            company_code="7203",
            company_name="トヨタ",
            title="決算短信",
            category=DisclosureCategory.EARNINGS,
            document_url="https://example.com/doc.pdf",
            exchange="東",
        )
        result = DisclosureList(
            total_count=1,
            disclosures=[d],
            query_date="2026-02-14",
        )

        data = result.to_dict()

        assert data["total_count"] == 1
        assert data["query_date"] == "2026-02-14"
        assert len(data["disclosures"]) == 1
        assert data["disclosures"][0]["company_code"] == "7203"
        assert data["disclosures"][0]["category"] == "earnings"

    def test_to_dict_empty(self) -> None:
        result = DisclosureList()
        data = result.to_dict()

        assert data["total_count"] == 0
        assert data["disclosures"] == []
