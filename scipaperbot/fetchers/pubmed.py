from datetime import datetime, timezone
from typing import List, Optional

import requests

from ..models import Paper

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_pubmed(
    keywords: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 100,
    email: Optional[str] = None,
) -> List[Paper]:
    term_parts = []
    for k in keywords:
        term_parts.append(f"({k}[Title/Abstract])")
    term = " OR ".join(term_parts) if term_parts else "biology[Title/Abstract]"
    date_range = f'("{start_date:%Y/%m/%d}"[Date - Publication] : "{end_date:%Y/%m/%d}"[Date - Publication])'
    query = f"({term}) AND {date_range}"

    params = {"db": "pubmed", "retmode": "json", "retmax": str(max_results), "term": query}
    if email:
        params["email"] = email

    r = requests.get(f"{BASE}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    summary = requests.get(
        f"{BASE}/esummary.fcgi", params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)}, timeout=30
    )
    summary.raise_for_status()
    result = summary.json()

    papers: List[Paper] = []
    for pid in ids:
        item = result["result"].get(pid)
        if not item:
            continue
        title = item.get("title", "")
        auths = [a.get("name", "") for a in item.get("authors", [])]
        pub = item.get("pubdate", "")
        try:
            if len(pub) >= 10:
                dt = datetime.strptime(pub[:10], "%Y %b %d").replace(tzinfo=timezone.utc)
            else:
                dt = datetime(int(pub[:4]), 1, 1, tzinfo=timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
        link = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
        doi = item.get("elocationid") if item.get("elocationid", "").startswith("doi:") else item.get("doi")
        papers.append(
            Paper(
                id=f"pmid:{pid}",
                title=title,
                authors=auths,
                summary="",
                published=dt,
                source="PubMed",
                link=link,
                doi=doi,
                categories=[],
            )
        )

    return papers
