from dotenv import load_dotenv

from scipaperbot.twitter import TwitterClient


def main():
    load_dotenv()
    client = TwitterClient()
    try:
        mode = client.get_mode()
    except Exception:
        mode = "unknown"
    print(f"Auth mode: {mode}")
    handle = client.verify()
    if handle:
        print(f"Authenticated as @{handle}")
    else:
        print("Twitter credentials missing or invalid.")


if __name__ == "__main__":
    main()
