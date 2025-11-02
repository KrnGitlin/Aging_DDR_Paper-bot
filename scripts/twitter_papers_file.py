import argparse
import os
from dotenv import load_dotenv
from scipaperbot.twitter import TwitterClient


def main():
    ap = argparse.ArgumentParser(description="Tweet titles and URLs from a text file (two lines per entry)")
    ap.add_argument("--file", default="output/titles_and_urls.txt", help="Path to the titles_and_urls.txt file")
    ap.add_argument("--limit", type=int, default=1, help="Max number of tweets to send (pairs)")
    ap.add_argument("--dry-run", action="store_true", help="Print instead of posting")
    args = ap.parse_args()

    load_dotenv()

    # Auth
    client = TwitterClient()
    mode = getattr(client, "get_mode", lambda: "unknown")()
    handle = client.verify()
    print(f"Auth mode: {mode}; handle: @{handle if handle else 'N/A'}")

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        return

    with open(args.file, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    count = 0
    for i in range(0, len(lines), 2):
        if count >= args.limit:
            break
        if i + 1 >= len(lines):
            print(f"Warning: dangling title without URL: {lines[i]}")
            break
        title = lines[i]
        url = lines[i + 1]
        tweet = f"{title}\n{url}"
        if args.dry_run:
            print("[DRY-RUN]", tweet)
        else:
            url_posted = client.post(tweet, dry_run=False)
            if url_posted:
                print(f"Posted: {url_posted}")
            else:
                print("Failed to post this entry; see previous logs.")
        count += 1

    print(f"Processed pairs: {count}")


if __name__ == "__main__":
    main()
