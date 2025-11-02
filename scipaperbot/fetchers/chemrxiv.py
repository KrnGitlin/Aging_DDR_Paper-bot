from datetime import datetime, timezone
from typing import List

import requests

from ..models import Paper


def fetch_chemrxiv(keywords: List[str], start_date: datetime, end_date: datetime, max_results: int = 100) -> List[Paper]:
    url = "https://api.crossref.org/works"
    params = {
        "filter": f"from-pub-date:{start_date:%Y-%m-%d},until-pub-date:{end_date:%Y-%m-%d},prefix:10.26434,type:posted-content",
        "rows": str(max_results),
        "sort": "issued",
        "order": "desc",
    }
    headers = {"User-Agent": "Aging-DDR-bot/1.0"}

    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    items = r.json().get("message", {}).get("items", [])

    papers: List[Paper] = []
    lower_keywords = [k.lower() for k in keywords]

    for it in items:
        title = " ".join(it.get("title", []))
        abstract = it.get("abstract", "")
        text = f"{title}\n{abstract}".lower()
        if lower_keywords and not any(k in text for k in lower_keywords):
            continue

        issued = it.get("issued", {}).get("date-parts", [[datetime.now().year, 1, 1]])[0]
        dt = datetime(
            issued[0],
            issued[1] if len(issued) > 1 else 1,
            issued[2] if len(issued) > 2 else 1,
            tzinfo=timezone.utc,
        )
        doi = it.get("DOI")
        link = it.get("URL", f"https://chemrxiv.org/engage/chemrxiv/article-details/{doi}")

        authors = []
        for a in it.get("author", []):
            nm = " ".join([a.get("given", ""), a.get("family", "")]).strip()
            if nm:
                authors.append(nm)

        papers.append(
            Paper(
                id=f"doi:{doi}" if doi else link,
                title=title,
                authors=authors,
                summary="",
                published=dt,
                source="ChemRxiv",
                link=link,
                doi=doi,
                categories=[],
            )
        )

    return papers
