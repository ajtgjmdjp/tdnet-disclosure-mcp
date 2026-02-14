"""Tests for tdnet-disclosure-mcp client."""

from datetime import date

import httpx
import pytest
import respx

from tdnet_disclosure_mcp.client import TdnetClient

_SAMPLE_RESPONSE = {
    "total_count": 2,
    "items": [
        {
            "Tdnet": {
                "id": "1001",
                "pubdate": "2026-02-14 15:30:00",
                "company_code": "72030",
                "company_name": "トヨタ自動車",
                "title": "2025年3月期 決算短信〔日本基準〕（連結）",
                "document_url": "https://example.com/doc1.pdf",
                "url_xbrl": "https://example.com/doc1.zip",
                "markets_string": "東",
                "update_history": None,
            }
        },
        {
            "Tdnet": {
                "id": "1002",
                "pubdate": "2026-02-14 16:00:00",
                "company_code": "67580",
                "company_name": "ソニーグループ",
                "title": "配当予想の修正に関するお知らせ",
                "document_url": "https://example.com/doc2.pdf",
                "url_xbrl": None,
                "markets_string": "東",
                "update_history": None,
            }
        },
    ],
}


class TestTdnetClientInit:
    """Test TdnetClient initialization."""

    def test_default_init(self) -> None:
        client = TdnetClient()
        assert client._timeout == 30.0
        assert client._http is None

    def test_custom_timeout(self) -> None:
        client = TdnetClient(timeout=60.0)
        assert client._timeout == 60.0


class TestTdnetClientRecent:
    """Test get_recent."""

    @respx.mock
    async def test_get_recent_success(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.get_recent(limit=50)

        assert result.total_count == 2
        assert len(result.disclosures) == 2
        assert result.disclosures[0].company_code == "7203"
        assert result.disclosures[0].company_name == "トヨタ自動車"

    @respx.mock
    async def test_get_recent_empty(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json={"total_count": 0, "items": []})
        )

        async with TdnetClient() as client:
            result = await client.get_recent()

        assert result.total_count == 0
        assert result.disclosures == []

    @respx.mock
    async def test_get_recent_limit_clamped(self) -> None:
        route = respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json={"total_count": 0, "items": []})
        )

        async with TdnetClient() as client:
            await client.get_recent(limit=999)

        assert route.called
        assert "300" in str(route.calls[0].request.url)


class TestTdnetClientByDate:
    """Test get_by_date."""

    @respx.mock
    async def test_get_by_date_success(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/20260214.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.get_by_date(date(2026, 2, 14))

        assert result.total_count == 2
        assert result.query_date == "2026-02-14"


class TestTdnetClientByDateRange:
    """Test get_by_date_range."""

    @respx.mock
    async def test_get_by_date_range_success(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/20260210-20260214.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.get_by_date_range(date(2026, 2, 10), date(2026, 2, 14))

        assert result.total_count == 2
        assert result.query_date == "2026-02-10 to 2026-02-14"


class TestTdnetClientByCode:
    """Test get_by_code."""

    @respx.mock
    async def test_get_by_code_success(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/7203.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.get_by_code("7203")

        assert result.total_count == 2
        assert result.disclosures[0].company_code == "7203"

    async def test_get_by_code_invalid(self) -> None:
        async with TdnetClient() as client:
            with pytest.raises(ValueError, match="4 digits"):
                await client.get_by_code("ABC")

    async def test_get_by_code_too_long(self) -> None:
        async with TdnetClient() as client:
            with pytest.raises(ValueError, match="4 digits"):
                await client.get_by_code("72030")


class TestTdnetClientSearch:
    """Test search."""

    @respx.mock
    async def test_search_by_name(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.search("トヨタ")

        assert result.total_count == 1
        assert result.disclosures[0].company_code == "7203"

    @respx.mock
    async def test_search_by_code(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.search("7203")

        assert result.total_count == 1

    @respx.mock
    async def test_search_by_title(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.search("決算短信")

        assert result.total_count == 1
        assert "決算短信" in result.disclosures[0].title

    @respx.mock
    async def test_search_no_match(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.search("存在しない企業")

        assert result.total_count == 0


class TestTdnetClientTestConnection:
    """Test test_connection."""

    @respx.mock
    async def test_success(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json={"items": [], "total_count": 0})
        )

        async with TdnetClient() as client:
            assert await client.test_connection() is True

    @respx.mock
    async def test_failure(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(500)
        )

        async with TdnetClient() as client:
            assert await client.test_connection() is False


class TestTdnetClientLifecycle:
    """Test client lifecycle."""

    async def test_close(self) -> None:
        client = TdnetClient()
        client._get_http_client()
        assert client._http is not None

        await client.close()
        assert client._http is None

    async def test_multiple_closes(self) -> None:
        client = TdnetClient()
        await client.close()
        await client.close()

    async def test_context_manager(self) -> None:
        async with TdnetClient() as client:
            assert client is not None
        assert client._http is None


class TestTdnetClientCategoryParsing:
    """Test that API responses get correct categories."""

    @respx.mock
    async def test_categories_from_api(self) -> None:
        respx.get("https://webapi.yanoshin.jp/webapi/tdnet/list/recent.json").mock(
            return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
        )

        async with TdnetClient() as client:
            result = await client.get_recent()

        assert result.disclosures[0].category.value == "earnings"
        assert result.disclosures[1].category.value == "dividend"
