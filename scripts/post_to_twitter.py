import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dotenv import load_dotenv

from scipaperbot.models import Paper
from scipaperbot.storage import load_papers
from scipaperbot.twitter import TwitterClient


def load_config(path: str) -> Dict:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compose_hashtags(p: Paper, max_hashtags: int = 4) -> List[str]:
    mapping = {
        "aging": "#aging",
        "ageing": "#aging",
        "dna damage": "#DNAdamage",
        "ddr": "#DDR",
        "senescence": "#senescence",
        "telomere": "#telomere",
        "telomerase": "#telomerase",
    }
    tags = []
    text = (p.title + "\n" + p.summary).lower()
    for key, tag in mapping.items():
        if key in text and tag not in tags:
            tags.append(tag)
        if len(tags) >= max_hashtags:
            break
    if not tags:
        tags = ["#biology"]
    return tags[:max_hashtags]


def truncate_to_limit(text: str, limit: int = 280) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def compose_tweet(p: Paper) -> str:
    tags = compose_hashtags(p)
    base = f"{p.title.strip()}\n{p.link}"
    tag_str = " ".join(tags)
    remaining = 280 - len(base) - 1
    if remaining > 10 and tag_str:
        text = f"{base} {tag_str}"
    else:
        text = base
    return truncate_to_limit(text)


def main():
    ap = argparse.ArgumentParser(description="Post a paper to Twitter")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--source", default=None, help="Only post from a specific source (e.g., bioRxiv)")
    ap.add_argument("--max-age-days", type=int, default=30, help="Only consider papers newer than this many days")
    ap.add_argument("--dry-run", action="store_true", help="Force dry-run regardless of config")
    args = ap.parse_args()

    cfg = load_config(args.config)

    # Load env vars if present
    load_dotenv()
    # Print non-sensitive auth readiness (booleans only)
    import os as _os
    auth_presence = {
        "TWITTER_CONSUMER_KEY": bool(_os.getenv("TWITTER_CONSUMER_KEY")),
        "TWITTER_CONSUMER_SECRET": bool(_os.getenv("TWITTER_CONSUMER_SECRET")),
        "TWITTER_ACCESS_TOKEN": bool(_os.getenv("TWITTER_ACCESS_TOKEN")),
        "TWITTER_ACCESS_TOKEN_SECRET": bool(_os.getenv("TWITTER_ACCESS_TOKEN_SECRET")),
        "TWITTER_CLIENT_ID": bool(_os.getenv("TWITTER_CLIENT_ID")),
        "TWITTER_CLIENT_SECRET": bool(_os.getenv("TWITTER_CLIENT_SECRET")),
        "TWITTER_REFRESH_TOKEN": bool(_os.getenv("TWITTER_REFRESH_TOKEN")),
    }
    print("Auth presence:", {k: ("set" if v else "missing") for k, v in auth_presence.items()})

    papers_path = cfg.get("site_data_path", os.path.join("site", "data", "papers.json"))
    papers = load_papers(papers_path)
    print(f"Loaded {len(papers)} papers from {papers_path}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.max_age_days)

    posted_state_path = os.path.join("data", "posted_ids.json")
    os.makedirs(os.path.dirname(posted_state_path), exist_ok=True)
    try:
        with open(posted_state_path, "r", encoding="utf-8") as f:
            posted_ids = set(json.load(f))
    except FileNotFoundError:
        posted_ids = set()

    # Compute eligibility counts for debugging
    newer = [p for p in papers if p.published >= cutoff]
    if args.source:
        newer = [p for p in newer if p.source == args.source]
    unposted = [p for p in newer if p.id not in posted_ids]
    print(
        f"Eligible after filters -> newer_than={args.max_age_days}d: {len(newer)}, unposted: {len(unposted)}, source={'any' if not args.source else args.source}"
    )

    candidate: Optional[Paper] = None
    for p in unposted:
        candidate = p
        break

    if not candidate:
        print("No candidate paper found to post.")
        return

    tweet_text = compose_tweet(candidate)
    print("Selected candidate:", candidate.title)
    print("Candidate link:", candidate.link)

    tw_enabled = bool(cfg.get("twitter", {}).get("enabled", False))
    dry_run = args.dry_run or (not tw_enabled) or bool(cfg.get("twitter", {}).get("dry_run", True))

    client = TwitterClient()
    try:
        mode = client.get_mode()
    except Exception:
        mode = "unknown"
    print(f"Auth mode: {mode}")
    handle = client.verify()
    if handle:
        print(f"Twitter auth OK as @{handle}")
    else:
        print("Twitter auth NOT verified (will still print tweet for dry-run)")

    url = client.post(tweet_text, dry_run=dry_run)
    if dry_run:
        print("[DRY-RUN] Would post:")
        print(tweet_text)
    else:
        if url:
            print(f"Posted: {url}")
        else:
            print("Tweet not sent: missing/invalid Twitter credentials or API failure.")

    # Only record as posted when an actual post happened
    if not dry_run and url:
        posted_ids.add(candidate.id)
        with open(posted_state_path, "w", encoding="utf-8") as f:
            json.dump(sorted(list(posted_ids)), f, indent=2)


if __name__ == "__main__":
    main()
