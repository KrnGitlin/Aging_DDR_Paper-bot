import os
from typing import Optional

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
        self.consumer_key = consumer_key or os.getenv("TWITTER_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("TWITTER_CONSUMER_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.client: Optional[tweepy.Client] = None
        self._username: Optional[str] = None
        self._auth()

    def _auth(self) -> None:
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            return
        # OAuth 1.0a user context with v2 Client
        self.client = tweepy.Client(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True,
        )

    def verify(self) -> Optional[str]:
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
        if dry_run or not self.client:
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
