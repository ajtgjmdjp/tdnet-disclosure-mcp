"""Tests for tdnet-disclosure-mcp CLI."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from click.testing import CliRunner

from tdnet_disclosure_mcp import __version__
from tdnet_disclosure_mcp.cli import cli
from tdnet_disclosure_mcp.models import (
    Disclosure,
    DisclosureCategory,
    DisclosureList,
)


def _mock_result() -> DisclosureList:
    """Create a mock result for testing."""
    return DisclosureList(
        total_count=1,
        disclosures=[
            Disclosure(
                id="1",
                pubdate=datetime(2026, 2, 14, 15, 30),
                company_code="7203",
                company_name="トヨタ自動車",
                title="決算短信",
                category=DisclosureCategory.EARNINGS,
                document_url="https://example.com/doc.pdf",
                exchange="東",
            )
        ],
    )


class TestCliVersion:
    """Test version command."""

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestCliLatest:
    """Test latest command."""

    def test_latest_success(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.get_recent = AsyncMock(return_value=_mock_result())
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["latest"])

        assert result.exit_code == 0
        assert "7203" in result.output
        assert "トヨタ" in result.output

    def test_latest_json(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.get_recent = AsyncMock(return_value=_mock_result())
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["latest", "--json-output"])

        assert result.exit_code == 0
        assert '"total_count"' in result.output


class TestCliSearch:
    """Test search command."""

    def test_search_success(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.search = AsyncMock(return_value=_mock_result())
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["search", "トヨタ"])

        assert result.exit_code == 0
        assert "トヨタ" in result.output


class TestCliCompany:
    """Test company command."""

    def test_company_success(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.get_by_code = AsyncMock(return_value=_mock_result())
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["company", "7203"])

        assert result.exit_code == 0
        assert "7203" in result.output


class TestCliByDate:
    """Test by-date command."""

    def test_by_date_success(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_result = DisclosureList(
                total_count=1,
                disclosures=[
                    Disclosure(
                        id="1",
                        pubdate=datetime(2026, 2, 14, 15, 30),
                        company_code="7203",
                        company_name="トヨタ自動車",
                        title="決算短信",
                        category=DisclosureCategory.EARNINGS,
                    )
                ],
                query_date="2026-02-14",
            )
            mock_client = Mock()
            mock_client.get_by_date = AsyncMock(return_value=mock_result)
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["by-date", "2026-02-14"])

        assert result.exit_code == 0
        assert "2026-02-14" in result.output


class TestCliTest:
    """Test test command."""

    def test_test_success(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.test_connection = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["test"])

        assert result.exit_code == 0
        assert "successful" in result.output

    def test_test_failure(self) -> None:
        runner = CliRunner()

        with patch("tdnet_disclosure_mcp.cli.TdnetClient") as mock_class:
            mock_client = Mock()
            mock_client.test_connection = AsyncMock(return_value=False)
            mock_client.close = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_class.return_value = mock_client

            result = runner.invoke(cli, ["test"])

        assert result.exit_code == 1
        assert "failed" in result.output
