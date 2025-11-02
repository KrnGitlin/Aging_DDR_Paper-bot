import os
from typing import Optional

import tweepy


class TwitterClient:
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
        self.api: Optional[tweepy.API] = None
        self._auth()

    def _auth(self) -> None:
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            return
        auth = tweepy.OAuth1UserHandler(
            self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret
        )
        self.api = tweepy.API(auth)

    def verify(self) -> Optional[str]:
        if not self.api:
            return None
        me = self.api.verify_credentials()
        return me.screen_name if me else None

    def post(self, text: str, dry_run: bool = True) -> Optional[str]:
        if dry_run or not self.api:
            return None
        status = self.api.update_status(status=text)
        return f"https://twitter.com/{status.user.screen_name}/status/{status.id}"
