"""Tests for tdnet-disclosure-mcp server."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

import tdnet_disclosure_mcp.server as server_module
from tdnet_disclosure_mcp.models import (
    Disclosure,
    DisclosureCategory,
    DisclosureList,
)


class TestServerHelpers:
    """Test server helper functions."""

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self) -> None:
        with (
            patch.object(server_module, "_client", None),
            patch("tdnet_disclosure_mcp.server.TdnetClient") as mock_class,
        ):
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            client = await server_module._get_client()
            assert client is mock_instance

    @pytest.mark.asyncio
    async def test_get_client_returns_existing(self) -> None:
        existing = Mock()
        with patch.object(server_module, "_client", existing):
            client = await server_module._get_client()
            assert client is existing


class TestServerInputValidation:
    """Test server input validation patterns."""

    def test_valid_stock_code_pattern(self) -> None:
        import re

        pattern = r"^\d{4}$"
        assert re.match(pattern, "7203")
        assert re.match(pattern, "0001")
        assert not re.match(pattern, "72030")
        assert not re.match(pattern, "ABC")

    def test_valid_date_pattern(self) -> None:
        import re

        pattern = r"^\d{4}-\d{2}-\d{2}$"
        assert re.match(pattern, "2026-02-14")
        assert not re.match(pattern, "2026/02/14")


class TestServerResultConversion:
    """Test server result conversion."""

    def test_disclosure_list_to_dict(self) -> None:
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
        result = DisclosureList(total_count=1, disclosures=[d])

        data = result.to_dict()
        assert data["total_count"] == 1
        assert data["disclosures"][0]["company_code"] == "7203"
        assert data["disclosures"][0]["category"] == "earnings"

    def test_empty_result_to_dict(self) -> None:
        result = DisclosureList()
        data = result.to_dict()
        assert data["total_count"] == 0
        assert data["disclosures"] == []
