import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import yaml

from scipaperbot.fetchers.arxiv import fetch_arxiv
from scipaperbot.fetchers.biorxiv import fetch_rxiv
from scipaperbot.fetchers.chemrxiv import fetch_chemrxiv
from scipaperbot.fetchers.pubmed import fetch_pubmed
from scipaperbot.storage import dedupe_and_sort, save_papers


BIO_HEURISTIC = re.compile(
    r"\b(cell|cells|mouse|mice|human|patient|tissue|protein|gene|genomic|rna|dna|biolog|organism|yeast|zebrafish)\b",
    re.I,
)


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def norm_keywords(keywords: List[str]) -> List[str]:
    # Include common biological variants
    aliases = {
        "aging": ["aging", "ageing"],
        "dna damage": ["dna damage", "dna repair", "double strand break", "dsb", "genotoxic"],
        "ddr": ["ddr", "dna damage response", "damage response"],
        "senescence": ["senescence", "cellular senescence", "senolytic", "senomorphic"],
        "telomere": ["telomere", "telomerase", "telomeres"],
    }
    extra = []
    for k in keywords:
        lk = k.lower()
        for base, al in aliases.items():
            if lk == base or lk in al:
                extra.extend(al)
    return sorted(set([k] + extra for k in keywords), key=lambda x: str(x))  # keep list stable


def compile_keyword_regex(keywords: List[str]) -> List[re.Pattern]:
    # word-boundary-ish regexes; allow hyphenation and plural forms where sensible
    patterns = []
    for k in keywords:
        k = k.strip()
        if not k:
            continue
        esc = re.escape(k)
        # allow minor variations for certain base terms
        if k.lower() in {"aging", "ageing"}:
            # Match both spellings: aging and ageing
            patterns.append(re.compile(r"\b(?:aging|ageing)\b", re.I))
        elif k.lower() == "ddr":
            patterns.append(re.compile(r"\b(?:ddr|dna\s+damage\s+response)\b", re.I))
        elif k.lower().startswith("dna damage"):
            patterns.append(re.compile(r"\bdna\s+damage(?:\s+response)?\b", re.I))
        else:
            patterns.append(re.compile(rf"\b{esc}\b", re.I))
    return patterns


def find_matches(text: str, patterns: List[re.Pattern]) -> List[str]:
    found = []
    for rx in patterns:
        if rx.search(text):
            found.append(rx.pattern)
    return found


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch and update papers.json for the site")
    ap.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)

    lookback_days = int(cfg.get("lookback_days", 7))
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=lookback_days)

    keywords: List[str] = cfg.get("keywords", [])
    exclude_keywords: List[str] = cfg.get("exclude_keywords", [])
    required_keywords: List[str] = cfg.get("required_keywords", [])

    kw_regex = compile_keyword_regex(keywords)
    excl_regex = compile_keyword_regex(exclude_keywords) if exclude_keywords else []
    req_regex = compile_keyword_regex(required_keywords) if required_keywords else []

    papers: List = []
    counts = {"arxiv": 0, "biorxiv": 0, "medrxiv": 0, "pubmed": 0, "chemrxiv": 0}

    sources = cfg.get("sources", {})

    def safe_call(name: str, func, *a, **kw):
        try:
            return func(*a, **kw)
        except Exception as e:
            print(f"[WARN] {name} failed: {e}")
            return []

    if sources.get("arxiv", {}).get("enabled", True):
        categories = sources.get("arxiv", {}).get("categories", ["q-bio*", "cs.CB"])
        ar = safe_call("arXiv", fetch_arxiv, keywords, start_date, now, 200, categories)
        counts["arxiv"] = len(ar)
        papers.extend(ar)

    if sources.get("biorxiv", {}).get("enabled", True):
        br = safe_call("bioRxiv", fetch_rxiv, "biorxiv", start_date, now, 1000)
        counts["biorxiv"] = len(br)
        papers.extend(br)

    if sources.get("medrxiv", {}).get("enabled", False):
        mr = safe_call("medRxiv", fetch_rxiv, "medrxiv", start_date, now, 1000)
        counts["medrxiv"] = len(mr)
        papers.extend(mr)

    if sources.get("pubmed", {}).get("enabled", True):
        pm = safe_call("PubMed", fetch_pubmed, keywords, start_date, now, 200, sources.get("pubmed", {}).get("email"))
        counts["pubmed"] = len(pm)
        papers.extend(pm)

    if sources.get("chemrxiv", {}).get("enabled", True):
        chem = safe_call("ChemRxiv", fetch_chemrxiv, keywords, start_date, now, 200)
        if sources.get("chemrxiv", {}).get("bio_only", True):
            chem = [p for p in chem if BIO_HEURISTIC.search((p.title + "\n" + p.summary))]
        counts["chemrxiv"] = len(chem)
        papers.extend(chem)

    # Filter for relevance by keywords with optional exclude/required logic (Scitify-like)
    filtered = []
    for p in papers:
        text = f"{p.title}\n{p.summary}"
        # Exclude if any exclude keyword matches
        if excl_regex and find_matches(text, excl_regex):
            continue
        # If required keywords present, require at least one match
        if req_regex and not find_matches(text, req_regex):
            continue
        # Finally require at least one general keyword
        matches = find_matches(text, kw_regex)
        if matches:
            p.keywords_matched = matches
            filtered.append(p)

    final = dedupe_and_sort(filtered)

    # Diagnostics
    total_raw = sum(counts.values())
    print(
        "Sources fetched counts:",
        f"arXiv={counts['arxiv']}",
        f"bioRxiv={counts['biorxiv']}",
        f"medRxiv={counts['medrxiv']}",
        f"PubMed={counts['pubmed']}",
        f"ChemRxiv={counts['chemrxiv']}",
        f"total_raw={total_raw}",
    )
    print(f"After filtering: kept={len(final)} of {total_raw}")

    # Write to site/data/papers.json
    site_path = cfg.get("site_data_path", os.path.join("site", "data", "papers.json"))
    save_papers(site_path, final)

    print(f"Wrote {len(final)} papers to {site_path}")


if __name__ == "__main__":
    main()
