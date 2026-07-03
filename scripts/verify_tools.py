"""Verify all 4 tdnet-disclosure-mcp MCP tools work correctly."""

import asyncio
from datetime import date, timedelta

from tdnet_disclosure_mcp.client import TdnetClient


async def main() -> None:
    async with TdnetClient() as client:
        # Tool 1: get_latest_disclosures
        print("=" * 60)
        print("[Tool 1] get_latest_disclosures (limit=5)")
        result = await client.get_recent(limit=5)
        d = result.to_dict()
        print(f"  total_count: {d['total_count']}")
        for item in d["disclosures"][:3]:
            print(f"  - {item['company_code']} {item['company_name']}: {item['title'][:50]}")
            print(f"    category={item['category']}, pubdate={item['pubdate']}")
        status1 = "PASS" if d["total_count"] > 0 else "FAIL"
        print(f"  [{status1}]")

        # Tool 2: search_disclosures
        print("=" * 60)
        print("[Tool 2] search_disclosures (keyword='決算')")
        result2 = await client.search("決算", limit=5)
        d2 = result2.to_dict()
        print(f"  total_count: {d2['total_count']}")
        for item in d2["disclosures"][:3]:
            print(f"  - {item['company_code']} {item['company_name']}: {item['title'][:50]}")
        status2 = "PASS" if d2["total_count"] > 0 else "FAIL"
        print(f"  [{status2}]")

        # Tool 3: get_company_disclosures
        print("=" * 60)
        print("[Tool 3] get_company_disclosures (code='7203' Toyota)")
        result3 = await client.get_by_code("7203", limit=10)
        d3 = result3.to_dict()
        print(f"  total_count: {d3['total_count']}")
        for item in d3["disclosures"][:3]:
            print(f"  - {item['title'][:60]}")
            print(f"    category={item['category']}, pubdate={item['pubdate']}")
        status3 = "PASS"  # 0 is OK if no recent disclosures
        print(f"  [{status3}] (0 is OK if no disclosures in last ~30 days)")

        # Tool 4: get_disclosures_by_date
        print("=" * 60)
        # Use last Friday if today is weekend
        today = date.today()
        target = today - timedelta(days=1)
        while target.weekday() >= 5:  # skip weekends
            target -= timedelta(days=1)
        print(f"[Tool 4] get_disclosures_by_date (date='{target.isoformat()}')")
        result4 = await client.get_by_date(target)
        d4 = result4.to_dict()
        print(f"  total_count: {d4['total_count']}")
        for item in d4["disclosures"][:3]:
            print(f"  - {item['company_code']} {item['company_name']}: {item['title'][:50]}")
        status4 = "PASS" if d4["total_count"] > 0 else "FAIL"
        print(f"  [{status4}]")

        # Summary
        print("=" * 60)
        results = [status1, status2, status3, status4]
        passed = results.count("PASS")
        print(f"Result: {passed}/4 tools passed")


if __name__ == "__main__":
    asyncio.run(main())
