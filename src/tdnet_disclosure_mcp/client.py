"""Async client for TDNET disclosures via Yanoshin API.

Data source: https://webapi.yanoshin.jp/tdnet/
This uses the free Yanoshin Web API which mirrors TDNET data.
No authentication required.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from datetime import date

import httpx
from loguru import logger
from pydantic import ValidationError

from tdnet_disclosure_mcp.models import Disclosure, DisclosureList

# Yanoshin API base URL
_BASE_URL = "https://webapi.yanoshin.jp/webapi/tdnet/list"

# HTTP timeout
_DEFAULT_TIMEOUT = 30.0

# Valid code pattern (4-digit stock code)
_VALID_CODE_RE = re.compile(r"^\d{4}$")

# Max results per request
_MAX_LIMIT = 300


class TdnetClient:
    """Async client for TDNET disclosures.

    Uses the Yanoshin Web API to fetch timely disclosure data
    from TDNET (Tokyo Stock Exchange).

    No authentication required.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={"Accept": "application/json"},
            )
        return self._http

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> TdnetClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def _api_get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Make API GET request."""
        client = self._get_http_client()
        url = f"{_BASE_URL}/{path}"
        logger.debug(f"GET {url}")

        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return cast("dict[str, Any]", resp.json())

    async def get_recent(self, limit: int = 50) -> DisclosureList:
        """Get most recent disclosures.

        Args:
            limit: Maximum number of results (1-300).

        Returns:
            List of recent disclosures.
        """
        limit = min(max(1, limit), _MAX_LIMIT)
        data = await self._api_get("recent.json", {"limit": str(limit)})
        return self._parse_response(data)

    async def get_by_date(self, target_date: date) -> DisclosureList:
        """Get disclosures for a specific date.

        Args:
            target_date: The date to query.

        Returns:
            List of disclosures for the date.
        """
        date_str = target_date.strftime("%Y%m%d")
        data = await self._api_get(f"{date_str}.json", {"limit": str(_MAX_LIMIT)})
        result = self._parse_response(data)
        result.query_date = target_date.isoformat()
        return result

    async def get_by_date_range(self, start_date: date, end_date: date) -> DisclosureList:
        """Get disclosures for a date range.

        Args:
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of disclosures in the date range.
        """
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        data = await self._api_get(f"{start_str}-{end_str}.json", {"limit": str(_MAX_LIMIT)})
        result = self._parse_response(data)
        result.query_date = f"{start_date.isoformat()} to {end_date.isoformat()}"
        return result

    async def get_by_code(self, code: str, limit: int = 50) -> DisclosureList:
        """Get disclosures for a specific company.

        Args:
            code: 4-digit stock code.
            limit: Maximum number of results (1-300).

        Returns:
            List of disclosures for the company.
        """
        if not _VALID_CODE_RE.match(code):
            raise ValueError(f"Invalid stock code: {code!r} (must be 4 digits)")

        limit = min(max(1, limit), _MAX_LIMIT)
        data = await self._api_get(f"{code}.json", {"limit": str(limit)})
        return self._parse_response(data)

    async def search(self, keyword: str, limit: int = 50) -> DisclosureList:
        """Search disclosures by keyword in title.

        Fetches recent disclosures and filters by keyword.

        Args:
            keyword: Search keyword.
            limit: Maximum number of results.

        Returns:
            Filtered list of disclosures.
        """
        # Fetch recent data then filter client-side
        data = await self._api_get("recent.json", {"limit": str(_MAX_LIMIT)})
        all_disclosures = self._parse_response(data)

        keyword_lower = keyword.lower()
        filtered = [
            d
            for d in all_disclosures.disclosures
            if keyword_lower in d.title.lower()
            or keyword_lower in d.company_name.lower()
            or keyword == d.company_code
        ][:limit]

        return DisclosureList(
            total_count=len(filtered),
            disclosures=filtered,
        )

    async def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection successful.
        """
        try:
            data = await self._api_get("recent.json", {"limit": "1"})
            return "items" in data
        except (httpx.HTTPError, KeyError):
            return False

    def _parse_response(self, data: dict[str, Any]) -> DisclosureList:
        """Parse API response into DisclosureList."""
        items = data.get("items", [])
        total = data.get("total_count", len(items))

        disclosures: list[Disclosure] = []
        for item in items:
            try:
                disclosures.append(Disclosure.from_api(item))
            except (ValidationError, ValueError):
                item_id = item.get("Tdnet", {}).get("id")
                logger.debug(f"Skipping invalid disclosure item: {item_id}")
                continue

        return DisclosureList(
            total_count=total,
            disclosures=disclosures,
        )
