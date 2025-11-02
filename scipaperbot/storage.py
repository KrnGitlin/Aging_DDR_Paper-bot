import json
import os
from typing import List
from .models import Paper


def load_papers(path: str) -> List[Paper]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Paper.from_dict(x) for x in data]
    except FileNotFoundError:
        return []


def save_papers(path: str, papers: List[Paper]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in papers], f, ensure_ascii=False, indent=2)


def dedupe_and_sort(papers: List[Paper]) -> List[Paper]:
    seen = {}
    for p in papers:
        if p.id not in seen or (seen[p.id].published < p.published):
            seen[p.id] = p
    return sorted(seen.values(), key=lambda p: p.published, reverse=True)
