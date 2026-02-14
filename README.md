# tdnet-disclosure-mcp

[![CI](https://github.com/ajtgjmdjp/tdnet-disclosure-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ajtgjmdjp/tdnet-disclosure-mcp/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/tdnet-disclosure-mcp.svg)](https://pypi.org/project/tdnet-disclosure-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for **TDNET timely disclosures (適時開示)** from the Tokyo Stock Exchange (JPX/TSE). Access earnings reports (決算短信), dividend announcements, buyback disclosures, forecast revisions, and more — no API key required.

Part of the [Japan Finance Data Stack](https://github.com/ajtgjmdjp/awesome-japan-finance-data): [edinet-mcp](https://github.com/ajtgjmdjp/edinet-mcp) (securities filings) | **tdnet-disclosure-mcp** (timely disclosures) | [estat-mcp](https://github.com/ajtgjmdjp/estat-mcp) (government statistics) | [boj-mcp](https://github.com/ajtgjmdjp/boj-mcp) (Bank of Japan) | [japan-news-mcp](https://github.com/ajtgjmdjp/japan-news-mcp) (financial news) | [jquants-mcp](https://github.com/ajtgjmdjp/jquants-mcp) (stock prices)

## Features

- **4 MCP Tools**: get_latest_disclosures, search_disclosures, get_company_disclosures, get_disclosures_by_date
- **No authentication required** - uses free public API
- **Auto-categorization**: earnings (決算短信), dividends, forecast revisions, buybacks, governance
- **CLI**: latest, search, company, by-date, test, serve

## Installation

```bash
pip install tdnet-disclosure-mcp
```

## Configuration

No API key required. Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "tdnet": {
      "command": "uvx",
      "args": ["tdnet-disclosure-mcp", "serve"]
    }
  }
}
```

## CLI Usage

```bash
# Get latest disclosures
tdnet-disclosure-mcp latest
tdnet-disclosure-mcp latest --limit 50

# Search disclosures
tdnet-disclosure-mcp search "トヨタ"
tdnet-disclosure-mcp search "決算短信"

# Get company disclosures
tdnet-disclosure-mcp company 7203

# Get disclosures by date
tdnet-disclosure-mcp by-date 2026-02-14

# Test API connection
tdnet-disclosure-mcp test

# Start MCP server
tdnet-disclosure-mcp serve
```

## MCP Tools

### get_latest_disclosures
Get the most recent TDNET disclosures.

Parameters:
- `limit`: Maximum results (1-300, default: 50)

### search_disclosures
Search by keyword (company name, stock code, or title).

Parameters:
- `keyword`: Search keyword
- `limit`: Maximum results (1-100, default: 20)

### get_company_disclosures
Get disclosures for a specific company.

Parameters:
- `code`: 4-digit stock code
- `limit`: Maximum results (1-300, default: 50)

### get_disclosures_by_date
Get all disclosures for a specific date.

Parameters:
- `target_date`: Date in YYYY-MM-DD format

## Disclosure Categories

| Category | Japanese | Examples |
|---|---|---|
| earnings | 決算短信 | Quarterly/annual earnings reports |
| dividend | 配当 | Dividend changes |
| forecast_revision | 業績予想修正 | Earnings forecast revisions |
| buyback | 自社株買い | Share buyback announcements |
| offering | 増資/新株 | Stock offerings |
| governance | ガバナンス | Corporate governance, board changes |
| other | その他 | Other disclosures |

## Data Source

Data is provided by the [Yanoshin Web API](https://webapi.yanoshin.jp/tdnet/), which mirrors TDNET (Tokyo Stock Exchange timely disclosure system). Only the last ~30 days of data are available.

## License

Apache-2.0
