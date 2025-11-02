import http.server
import socketserver
import threading
import webbrowser
import os
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
import tweepy

PORT = 8080
REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"
SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]


def main():
    load_dotenv()
    client_id = os.getenv("TWITTER_CLIENT_ID")
    client_secret = os.getenv("TWITTER_CLIENT_SECRET")
    if not client_id:
        print("Missing TWITTER_CLIENT_ID in environment.")
        return
    if not client_secret:
        print("Warning: TWITTER_CLIENT_SECRET missing. If your app is a confidential client, provide it.")

    oauth2 = tweepy.OAuth2UserHandler(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=client_secret,
    )

    auth_url = oauth2.get_authorization_url()
    print("Open this URL to authorize:")
    print(auth_url)

    code_holder = {"code": None}

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/callback":
                qs = parse_qs(parsed.query)
                code = (qs.get("code") or [None])[0]
                code_holder["code"] = code
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization received.</h1><p>You can close this window.</p>")
            else:
                self.send_response(404)
                self.end_headers()

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print(f"Waiting for redirect on {REDIRECT_URI} ...")
    while code_holder["code"] is None:
        pass

    httpd.shutdown()

    code = code_holder["code"]
    if not code:
        print("No code received")
        return

    try:
        token = oauth2.fetch_token(code=code)
    except Exception as e:
        print("Error exchanging code for token:", e)
        return

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    expires_in = token.get("expires_in")

    print("\nTokens obtained:")
    print("TWITTER_ACCESS_TOKEN:", access_token)
    print("TWITTER_REFRESH_TOKEN:", refresh_token)
    print("expires_in:", expires_in)
    print("\nNext steps:")
    print("1) Add TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET (if used), and TWITTER_REFRESH_TOKEN to your GitHub Actions secrets.")
    print("2) Our workflows will use OAuth 2.0 automatically if these are present. We do not persist rotated refresh tokens.")


if __name__ == "__main__":
    main()
