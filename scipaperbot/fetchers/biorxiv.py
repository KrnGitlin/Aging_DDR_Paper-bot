from datetime import datetime, timezone
from typing import List

import requests

from ..models import Paper


def fetch_rxiv(server: str, start_date: datetime, end_date: datetime, max_results: int = 1000) -> List[Paper]:
    """Fetch from bioRxiv or medRxiv via api.biorxiv.org.

    server: 'biorxiv' or 'medrxiv'
    """
    s = start_date.strftime("%Y-%m-%d")
    e = end_date.strftime("%Y-%m-%d")
    base = f"https://api.biorxiv.org/details/{server}/{s}/{e}"
    cursor = 0
    size = 100
    results: List[Paper] = []
    headers = {"User-Agent": "Aging-DDR-bot/1.0"}

    while True:
        url = f"{base}/{cursor}"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        js = r.json()
        collection = js.get("collection", [])

        for item in collection:
            pub = datetime.strptime(item["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            pid = item.get("doi", item.get("biorxiv_url", item.get("medrxiv_url", "")))
            link = (
                f"https://www.biorxiv.org/content/{item['doi']}"
                if server == "biorxiv"
                else f"https://www.medrxiv.org/content/{item['doi']}"
            )
            authors = [a.strip() for a in item.get("authors", "").split(";") if a.strip()]

            results.append(
                Paper(
                    id=pid,
                    title=item.get("title", ""),
                    authors=authors,
                    summary=item.get("abstract", ""),
                    published=pub,
                    source="bioRxiv" if server == "biorxiv" else "medRxiv",
                    link=link,
                    doi=item.get("doi"),
                    categories=[],
                )
            )

            if len(results) >= max_results:
                return results

        if len(collection) < size:
            break
        cursor += size

    return results
