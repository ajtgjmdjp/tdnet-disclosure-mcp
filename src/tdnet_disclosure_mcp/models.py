"""Domain models for tdnet-disclosure-mcp."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DisclosureCategory(str, Enum):
    """Disclosure category types."""

    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    FORECAST_REVISION = "forecast_revision"
    BUYBACK = "buyback"
    OFFERING = "offering"
    GOVERNANCE = "governance"
    OTHER = "other"


# Keywords for categorizing disclosures by title
_CATEGORY_PATTERNS: list[tuple[re.Pattern[str], DisclosureCategory]] = [
    (re.compile(r"決算短信|四半期報告|決算補足"), DisclosureCategory.EARNINGS),
    (re.compile(r"配当"), DisclosureCategory.DIVIDEND),
    (re.compile(r"業績予想.*修正|通期.*修正|予想.*変更"), DisclosureCategory.FORECAST_REVISION),
    (re.compile(r"自己株式|自社株"), DisclosureCategory.BUYBACK),
    (re.compile(r"新株|増資|公募"), DisclosureCategory.OFFERING),
    (re.compile(r"ガバナンス|役員|取締役"), DisclosureCategory.GOVERNANCE),
]


def _categorize(title: str) -> DisclosureCategory:
    """Categorize a disclosure by its title."""
    for pattern, category in _CATEGORY_PATTERNS:
        if pattern.search(title):
            return category
    return DisclosureCategory.OTHER


class Disclosure(BaseModel):
    """A single TDNET disclosure entry.

    Attributes:
        id: Unique disclosure ID.
        pubdate: Publication datetime.
        company_code: 4-digit stock code.
        company_name: Company name.
        title: Disclosure title.
        document_url: URL to the PDF document.
        xbrl_url: URL to XBRL data (may be None).
        exchange: Listed exchange(s).
        category: Auto-detected disclosure category.
        update_history: Update history text (usually empty).
    """

    id: str = Field(..., max_length=20)
    pubdate: datetime
    company_code: str = Field(..., pattern=r"^\d{4,5}$", max_length=5)
    company_name: str = Field(..., max_length=200)
    title: str = Field(..., max_length=500)
    document_url: str | None = Field(None, max_length=500)
    xbrl_url: str | None = Field(None, max_length=500)
    exchange: str = Field(default="", max_length=20)
    category: DisclosureCategory = Field(default=DisclosureCategory.OTHER)
    update_history: str | None = Field(None, max_length=500)

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> Disclosure:
        """Create from Yanoshin API response item."""
        tdnet = item.get("Tdnet", item)
        code_raw = tdnet.get("company_code", "")
        # Strip trailing "0" from 5-digit code
        code = code_raw[:4] if len(code_raw) == 5 else code_raw
        title = tdnet.get("title", "")

        return cls(
            id=str(tdnet.get("id", "")),
            pubdate=datetime.fromisoformat(tdnet.get("pubdate", "2000-01-01")),
            company_code=code,
            company_name=tdnet.get("company_name", "").strip(),
            title=title,
            document_url=tdnet.get("document_url"),
            xbrl_url=tdnet.get("url_xbrl"),
            exchange=tdnet.get("markets_string", ""),
            category=_categorize(title),
            update_history=tdnet.get("update_history"),
        )


class DisclosureList(BaseModel):
    """List of disclosures with metadata.

    Attributes:
        total_count: Total number of matching disclosures.
        disclosures: List of disclosure entries.
        query_date: Query date string (if date-filtered).
    """

    total_count: int = Field(0, ge=0)
    disclosures: list[Disclosure] = Field(default_factory=list)
    query_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MCP response."""
        return {
            "total_count": self.total_count,
            "query_date": self.query_date,
            "disclosures": [
                {
                    "id": d.id,
                    "pubdate": d.pubdate.isoformat(),
                    "company_code": d.company_code,
                    "company_name": d.company_name,
                    "title": d.title,
                    "category": d.category.value,
                    "document_url": d.document_url,
                    "exchange": d.exchange,
                }
                for d in self.disclosures
            ],
        }
