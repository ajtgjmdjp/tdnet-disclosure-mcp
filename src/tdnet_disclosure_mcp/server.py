"""MCP server exposing TDNET disclosure tools to LLMs via FastMCP.

Usage with Claude Desktop (add to ``claude_desktop_config.json``)::

    {
      "mcpServers": {
        "tdnet": {
          "command": "uvx",
          "args": ["tdnet-disclosure-mcp", "serve"]
        }
      }
    }

Data source: Yanoshin Web API (https://webapi.yanoshin.jp/tdnet/)
No authentication required.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import date
from typing import TYPE_CHECKING, Annotated, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from fastmcp import FastMCP
from pydantic import BeforeValidator, Field

from tdnet_disclosure_mcp.client import TdnetClient


def _coerce_str(v: Any) -> str | None:
    """Coerce int to str — MCP clients may send numeric values as int."""
    if v is None:
        return None
    return str(v)


# Lazily initialized client
_client: TdnetClient | None = None
_client_lock = asyncio.Lock()


async def _get_client() -> TdnetClient:
    """Return the shared TdnetClient, creating it on first call."""
    global _client
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is None:
            _client = TdnetClient()
    return _client


@asynccontextmanager
async def _lifespan(server: FastMCP[dict[str, Any]]) -> AsyncIterator[dict[str, Any]]:
    """Manage TdnetClient lifecycle."""
    global _client
    yield {}
    if _client is not None:
        await _client.close()
        _client = None


mcp = FastMCP(
    name="TDNET",
    lifespan=_lifespan,
    instructions=(
        "TDNET MCP server provides tools for accessing Japanese timely disclosures "
        "(適時開示情報) from the Tokyo Stock Exchange.\n\n"
        "Available tools:\n"
        "- get_latest_disclosures: Get today's or recent disclosures\n"
        "- search_disclosures: Search by keyword or company name\n"
        "- get_company_disclosures: Get disclosures for a specific company\n"
        "- get_disclosures_by_date: Get disclosures for a specific date\n\n"
        "Disclosure categories: earnings (決算短信), dividend (配当), "
        "forecast_revision (業績予想修正), buyback (自社株買い), offering (増資), "
        "governance (ガバナンス), other.\n\n"
        "Data source: TDNET via Yanoshin Web API. No authentication required.\n"
        "Note: Only the last ~30 days of data are available."
    ),
)


@mcp.tool()
async def get_latest_disclosures(
    limit: Annotated[
        int,
        Field(description="Maximum results (default: 50, max: 300)", ge=1, le=300),
    ] = 50,
) -> dict[str, Any]:
    """Get the most recent TDNET disclosures.

    Returns the latest timely disclosures from the Tokyo Stock Exchange,
    including earnings reports (決算短信), dividend changes, forecast revisions,
    stock buybacks, and other corporate announcements.

    Each disclosure includes company code, name, title, category, and document URL.
    """
    client = await _get_client()
    result = await client.get_recent(limit=limit)
    return result.to_dict()


@mcp.tool()
async def search_disclosures(
    keyword: Annotated[
        str,
        Field(
            description="Search keyword (company name, code, or disclosure title)",
            max_length=100,
        ),
    ],
    limit: Annotated[
        int,
        Field(description="Maximum results (default: 20)", ge=1, le=100),
    ] = 20,
) -> dict[str, Any]:
    """Search TDNET disclosures by keyword.

    Searches recent disclosures by company name, stock code, or title keyword.
    Examples: "トヨタ", "7203", "決算短信", "配当"
    """
    client = await _get_client()
    result = await client.search(keyword, limit=limit)
    return result.to_dict()


@mcp.tool()
async def get_company_disclosures(
    code: Annotated[
        str,
        BeforeValidator(_coerce_str),
        Field(
            description="4-digit stock code (e.g., '7203' for Toyota)",
            pattern=r"^\d{4}$",
            max_length=4,
        ),
    ],
    limit: Annotated[
        int,
        Field(description="Maximum results (default: 50)", ge=1, le=300),
    ] = 50,
) -> dict[str, Any]:
    """Get disclosures for a specific company.

    Returns all recent disclosures for the specified company,
    including earnings, dividends, forecast revisions, etc.

    Example: get_company_disclosures("7203") → Toyota's disclosures
    """
    client = await _get_client()
    result = await client.get_by_code(code, limit=limit)
    return result.to_dict()


@mcp.tool()
async def get_disclosures_by_date(
    target_date: Annotated[
        str,
        Field(
            description="Date in YYYY-MM-DD format",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            max_length=10,
        ),
    ],
) -> dict[str, Any]:
    """Get all disclosures for a specific date.

    Returns all TDNET disclosures filed on the specified date.
    Note: Only the last ~30 days are available.

    Example: get_disclosures_by_date("2026-02-14")
    """
    client = await _get_client()
    parsed_date = date.fromisoformat(target_date)
    result = await client.get_by_date(parsed_date)
    return result.to_dict()
