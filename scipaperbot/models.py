from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


@dataclass
class Paper:
    id: str
    title: str
    authors: List[str]
    summary: str
    published: datetime
    updated: Optional[datetime] = None
    source: str = ""
    link: str = ""
    doi: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    keywords_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "summary": self.summary,
            "published": self.published.replace(tzinfo=timezone.utc).isoformat(),
            "updated": self.updated.replace(tzinfo=timezone.utc).isoformat() if self.updated else None,
            "source": self.source,
            "link": self.link,
            "doi": self.doi,
            "categories": self.categories,
            "keywords_matched": self.keywords_matched,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Paper":
        def parse_dt(s):
            if not s:
                return None
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00"))
            except Exception:
                from dateutil import parser as dateparser
                return dateparser.parse(s)

        return Paper(
            id=d["id"],
            title=d.get("title", ""),
            authors=d.get("authors", []),
            summary=d.get("summary", ""),
            published=parse_dt(d.get("published")) or datetime.now(timezone.utc),
            updated=parse_dt(d.get("updated")) if d.get("updated") else None,
            source=d.get("source", ""),
            link=d.get("link", ""),
            doi=d.get("doi"),
            categories=d.get("categories", []),
            keywords_matched=d.get("keywords_matched", []),
        )
