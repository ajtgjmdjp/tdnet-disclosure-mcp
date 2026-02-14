"""CLI for tdnet-disclosure-mcp."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date

import click
from loguru import logger

from tdnet_disclosure_mcp import __version__
from tdnet_disclosure_mcp.client import TdnetClient


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """TDNET Disclosure MCP - Japanese timely disclosure tool."""
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="WARNING")


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"tdnet-disclosure-mcp {__version__}")


@cli.command()
@click.option("--limit", "-l", default=20, help="Maximum results (default: 20)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def latest(limit: int, json_output: bool) -> None:
    """Get latest disclosures."""

    async def _latest() -> None:
        async with TdnetClient() as client:
            result = await client.get_recent(limit=limit)

            if json_output:
                click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                click.echo(f"Latest disclosures ({result.total_count} total)\n")
                for d in result.disclosures:
                    time_str = d.pubdate.strftime("%H:%M")
                    click.echo(f"  [{time_str}] {d.company_code} {d.company_name}")
                    click.echo(f"    {d.title}")
                    click.echo(f"    [{d.category.value}]")
                    click.echo()

    asyncio.run(_latest())


@cli.command()
@click.argument("keyword")
@click.option("--limit", "-l", default=20, help="Maximum results (default: 20)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def search(keyword: str, limit: int, json_output: bool) -> None:
    """Search disclosures by keyword."""

    async def _search() -> None:
        async with TdnetClient() as client:
            result = await client.search(keyword, limit=limit)

            if json_output:
                click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                click.echo(f'Search results for: "{keyword}" ({result.total_count} found)\n')
                for d in result.disclosures:
                    time_str = d.pubdate.strftime("%Y-%m-%d %H:%M")
                    click.echo(f"  [{time_str}] {d.company_code} {d.company_name}")
                    click.echo(f"    {d.title}")
                    click.echo(f"    [{d.category.value}]")
                    click.echo()

    asyncio.run(_search())


@cli.command()
@click.argument("code")
@click.option("--limit", "-l", default=20, help="Maximum results (default: 20)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def company(code: str, limit: int, json_output: bool) -> None:
    """Get disclosures for a specific company (by stock code)."""

    async def _company() -> None:
        async with TdnetClient() as client:
            result = await client.get_by_code(code, limit=limit)

            if json_output:
                click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                click.echo(f"Disclosures for {code} ({result.total_count} total)\n")
                for d in result.disclosures:
                    time_str = d.pubdate.strftime("%Y-%m-%d %H:%M")
                    click.echo(f"  [{time_str}] {d.company_name}")
                    click.echo(f"    {d.title}")
                    click.echo(f"    [{d.category.value}]")
                    click.echo()

    asyncio.run(_company())


@cli.command()
@click.argument("target_date")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def by_date(target_date: str, json_output: bool) -> None:
    """Get disclosures for a specific date (YYYY-MM-DD)."""

    async def _by_date() -> None:
        async with TdnetClient() as client:
            parsed = date.fromisoformat(target_date)
            result = await client.get_by_date(parsed)

            if json_output:
                click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                click.echo(f"Disclosures for {target_date} ({result.total_count} total)\n")
                for d in result.disclosures:
                    time_str = d.pubdate.strftime("%H:%M")
                    click.echo(f"  [{time_str}] {d.company_code} {d.company_name}")
                    click.echo(f"    {d.title}")
                    click.echo()

    asyncio.run(_by_date())


@cli.command()
def test() -> None:
    """Test TDNET API connection."""

    async def _test() -> None:
        async with TdnetClient() as client:
            click.echo("Testing TDNET (Yanoshin API) connection...")

            if await client.test_connection():
                click.echo(click.style("Connection successful!", fg="green"))
            else:
                click.echo(click.style("Connection failed", fg="red"))
                sys.exit(1)

    asyncio.run(_test())


@cli.command()
@click.option("--transport", "-t", default="stdio", help="Transport type (stdio or sse)")
@click.option("--port", "-p", default=8000, help="Port for SSE transport")
def serve(transport: str, port: int) -> None:
    """Start the MCP server."""
    from tdnet_disclosure_mcp.server import mcp

    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    cli()
