from datetime import datetime, timezone
from typing import List, Optional

import feedparser
import requests

from ..models import Paper


def _build_query(keywords: List[str], categories: Optional[List[str]]) -> str:
    terms = []
    if keywords:
        kw_query = " OR ".join([f'(ti:"{k}" OR abs:"{k}")' for k in keywords])
        terms.append(f"({kw_query})")
    if categories:
        cat_query = " OR ".join([f"cat:{c}" for c in categories])
        terms.append(f"({cat_query})")
    return " AND ".join(terms) if terms else "all:biology"


essential_headers = {"User-Agent": "Aging-DDR-bot/1.0 (+https://github.com/KrnGitlin/Aging-DDR-papers-bot)"}


def fetch_arxiv(
    keywords: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 100,
    categories: Optional[List[str]] = None,
) -> List[Paper]:
    categories = categories or ["q-bio*", "cs.CB"]
    search_query = _build_query(keywords, categories)

    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": max_results,
    }

    r = requests.get(url, params=params, headers=essential_headers, timeout=30)
    r.raise_for_status()

    feed = feedparser.parse(r.text)
    papers: List[Paper] = []
    for e in feed.entries:
        pub = (
            datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            if getattr(e, "published_parsed", None)
            else datetime.now(timezone.utc)
        )
        if pub < start_date or pub > end_date:
            continue
        link = getattr(e, "link", "")
        authors = [a.name for a in getattr(e, "authors", [])]
        cats = [t.term for t in getattr(e, "tags", [])]
        pid = getattr(e, "id", link)

        papers.append(
            Paper(
                id=pid,
                title=e.title,
                authors=authors,
                summary=getattr(e, "summary", ""),
                published=pub,
                updated=None,
                source="arXiv",
                link=link,
                doi=None,
                categories=cats,
            )
        )

    return papers
