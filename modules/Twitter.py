import tweepy
from logging import getLogger
from modules.Models import sia_classify, Preprocess
Logger = getLogger(__name__)


class Twitter:
    '''soon..'''

    def __init__(self, populate_db, model=None):
        self._api_key = ""
        self._api_key_secret = ""
        self._bearer_token = ""
        self._access_token = ""
        self._access_token_secret = ""
        self.model = model
        self.populate_db = populate_db
        auth = tweepy.OAuthHandler(self._api_key, self._api_key_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        self.api = tweepy.API(auth,
                              wait_on_rate_limit=True,
                              retry_count=10,
                              retry_delay=15,
                              timeout=30)

    def build_query(self, ticker: str) -> str:
        '''Build a twitter search query using specific filters.

        Args:
            stock (str): _description_

        Returns:
            str: _description_
        '''
        symbols = ['$']
        query = ""
        for symbol in symbols:
            query += f'{symbol}{ticker.upper()} OR {symbol}{ticker.capitalize()} OR {symbol}{ticker.lower()} OR '
        query = query[:-3] + \
            "lang:en exclude:retweets -filter:replies -filter:links"
        Logger.debug("Query created: %s", query)
        return query

    def is_advertisement(self, tweet) -> bool:
        '''_summary_

        Args:
            tweet (_type_): _description_

        Returns:
            bool: _description_
        '''
        key_words = ["discord", "telegram"]

        for word in key_words:
            if word in tweet:
                return True
        return False

    def fetch_tweets_and_classify(self, ticker: str) -> list:
        '''Retrieve tweets based on a ticker and classify it as either positive/neutral/negative

        Args:
            ticker (str): _description_
            since_id (_type_): _description_

        Returns:
            list: _description_
        '''
        tweets = []
        for tweet in tweepy.Cursor(self.api.search_tweets,
                                   q=self.build_query(ticker),
                                   tweet_mode='extended',
                                   include_entities=False,
                                   result_type='recent',
                                   count=100
                                   ).items():
            try:
                tweet_content = {
                    "ID": tweet.id_str,
                    "Ticker": ticker.upper(),
                    "Text": tweet.full_text,
                    "Date": str(tweet.created_at).split("+")[0],
                }
                if tweet.user.followers_count < 5:
                    Logger.warning(
                        "Tweeter does not meet minimum follower requirement (Followers: %s)", tweet.user.followers_count)
                    continue
                if "bot" in str(tweet.user.screen_name).lower() or "alert" in str(tweet.user.screen_name).lower():
                    Logger.warning(
                        "Tweeter may be a bot account so not including (Name: %s)", tweet.user.screen_name)
                    continue
                if self.is_advertisement(tweet.full_text):
                    Logger.warning(
                        "Tweet is most likely an advertisement so skipping => %s", tweet.full_text)
                    continue
                cleaned_tweet = Preprocess.clean_text(tweet.full_text)
                if self.populate_db:
                    tweet_content["Sentiment"] = sia_classify(cleaned_tweet)
                else:
                    tweet_content["Sentiment"] = self.model.classify(
                        cleaned_tweet)

                if len(cleaned_tweet.strip()) <= 2:
                    Logger.warning("Cleaned tweet was too small to be indexed")
                    continue

                Logger.info("Retrieved tweet:\n%s", tweet_content)
                tweets.append(tweet_content)
            except Exception as err:
                Logger.warning(err)
        Logger.debug("Successfully retrieved %s tweets.", len(tweets))
        return tweets
