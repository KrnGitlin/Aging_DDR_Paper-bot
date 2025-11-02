from dotenv import load_dotenv

from scipaperbot.twitter import TwitterClient


def main():
    load_dotenv()
    client = TwitterClient()
    handle = client.verify()
    if handle:
        print(f"Authenticated as @{handle}")
    else:
        print("Twitter credentials missing or invalid.")


if __name__ == "__main__":
    main()
