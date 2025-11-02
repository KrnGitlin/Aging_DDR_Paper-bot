import base64
import os
from typing import Optional

import requests
import tweepy


class TwitterClient:
    """
    Twitter API v2 client using Tweepy.Client with OAuth 1.0a user context.

    We intentionally keep the same 4-secret auth model so existing GitHub
    Actions secrets continue to work. This posts via v2 create_tweet.
    """

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ) -> None:
        # OAuth 1.0a (legacy) secrets - still supported as fallback
        self.consumer_key = consumer_key or os.getenv("TWITTER_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("TWITTER_CONSUMER_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        # OAuth 2.0 user context (preferred)
        self.client_id = os.getenv("TWITTER_CLIENT_ID")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET")
        self.refresh_token = os.getenv("TWITTER_REFRESH_TOKEN")
        self._oauth2_access_token: Optional[str] = None

        self.client: Optional[tweepy.Client] = None
        self._username: Optional[str] = None

        # Prefer OAuth2 if creds exist, else fallback to OAuth1 via Tweepy Client
        if self.client_id and self.refresh_token:
            self._auth_oauth2()
        else:
            self._auth_oauth1()

    def _auth_oauth1(self) -> None:
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            return
        self.client = tweepy.Client(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True,
        )

    def _auth_oauth2(self) -> None:
        # Use refresh token to obtain an access token for user context (v2)
        token_url = "https://api.twitter.com/2/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth = None
        # Prefer Basic auth for confidential client if client_secret is available
        if self.client_secret:
            basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {basic}"
        try:
            resp = requests.post(token_url, data=data, headers=headers, timeout=20)
            if resp.status_code != 200:
                return
            token_json = resp.json()
            self._oauth2_access_token = token_json.get("access_token")
            # Note: Some providers rotate refresh_token here; we do NOT persist it from CI for security.
        except requests.RequestException:
            return

    def verify(self) -> Optional[str]:
        # OAuth2 path via REST if we have an access token
        if self._oauth2_access_token:
            try:
                resp = requests.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {self._oauth2_access_token}"},
                    timeout=20,
                )
                if resp.status_code != 200:
                    return None
                data = resp.json().get("data") or {}
                self._username = data.get("username")
                return self._username
            except requests.RequestException:
                return None

        # Fallback to Tweepy Client (OAuth1 in v2 client)
        if not self.client:
            return None
        try:
            me = self.client.get_me()
            if me and me.data and hasattr(me.data, "username"):
                self._username = me.data.username
                return self._username
            return None
        except tweepy.TweepyException:
            return None

    def post(self, text: str, dry_run: bool = True) -> Optional[str]:
        if dry_run:
            return None

        # OAuth2 POST /2/tweets
        if self._oauth2_access_token:
            try:
                resp = requests.post(
                    "https://api.twitter.com/2/tweets",
                    headers={
                        "Authorization": f"Bearer {self._oauth2_access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"text": text},
                    timeout=20,
                )
                if resp.status_code not in (200, 201):
                    return None
                data = resp.json().get("data") or {}
                tweet_id = data.get("id")
                if not tweet_id:
                    return None
                if not self._username:
                    self.verify()
                username = self._username or "i"
                return f"https://twitter.com/{username}/status/{tweet_id}"
            except requests.RequestException:
                return None

        # Fallback: Tweepy v2 client with OAuth1 creds
        if not self.client:
            return None
        try:
            resp = self.client.create_tweet(text=text)
            if not resp or not resp.data or "id" not in resp.data:
                return None
            tweet_id = resp.data["id"]
            if not self._username:
                self.verify()
            username = self._username or "i"
            return f"https://twitter.com/{username}/status/{tweet_id}"
        except tweepy.TweepyException:
            return None
