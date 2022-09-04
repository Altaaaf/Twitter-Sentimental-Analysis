from logging import getLogger
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from nltk.stem.snowball import SnowballStemmer
import re
import emoji
Logger = getLogger(__name__)

TICKERS = {
    'bbby',
    'bb',
    'nok',
    'pltr',
    'spce',
    'gme',
    'amc',
    'koss',
    'bbig',
    'aapl',
    'amzn',
    'tsla',
    'fb',
    'googl',
    'nflx'
}
nltk.download('vader_lexicon')
STOP_WORDS = set(stopwords.words('english'))
STOP_WORDS.update(TICKERS)
STOP_WORDS.update({'rt', 'retweet', 'RT', 'Retweet', 'RETWEET'})
STOP_WORDS.remove('not')
SENTIMENT_ANALYZER = SentimentIntensityAnalyzer()
STEMMER = SnowballStemmer(language='english')


class Preprocess:
    '''Preprocessor'''
    NEGATION_WORDS = ['dont', 'not', 'never']

    @staticmethod
    def clean_text(text, debug=False):
        '''Apply various string manipulation and NLP techniques to remove / add text to input

        Args:
            text (_type_): _description_
            debug (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        '''

        text = text.lower()
        text = Preprocess.replace_phrases(text)
        text = Preprocess.remove_tickers_mentions_hashtags(text)
        text = Preprocess.remove_links(text)

        tokens = word_tokenize(text)

        tokens = Preprocess.remove_stopwords_and_non_alphabet(tokens)
        tokens = Preprocess.stem_tokens(tokens)
        tokens = Preprocess.convert_negation_phrases(tokens)

        text = ' '.join(tokens)
        if debug:
            Logger.info("Preprocessed text:\n%s", text)
        return text

    @staticmethod
    def remove_emojis(text):
        '''Remove emojis

        Args:
            text (_type_): _description_

        Returns:
            _type_: _description_
        '''
        try:
            return emoji.get_emoji_regexp().sub(r'', text)
        except:
            return text

    @staticmethod
    def stem_tokens(tokens):
        '''Apply stemmer to every token

        Args:
            tokens (_type_): _description_

        Returns:
            _type_: _description_
        '''
        return [STEMMER.stem(word) for word in tokens]

    @staticmethod
    def convert_negation_phrases(tokens):
        '''Convert phrases that are meant to be negated to give better context/sentiment

        Args:
            tokens (_type_): _description_

        Returns:
            _type_: _description_
        '''
        while True:
            idx_to_remove = None
            for index, token in enumerate(tokens):
                if token in Preprocess.NEGATION_WORDS and index + 1 < len(tokens) and tokens[index+1] not in Preprocess.NEGATION_WORDS:
                    # check to see if not_ already inside token before adding it
                    new_token = ""
                    if "not_" in tokens[index+1]:
                        tokens[index+1].replace('not_', '')
                        new_token = tokens[index+1].replace('not_', '')
                    else:
                        new_token = "not_" + tokens[index+1]
                    tokens[index+1] = new_token.strip()
                    idx_to_remove = index
                    break
            if idx_to_remove is None:
                break
            tokens.pop(idx_to_remove)
            idx_to_remove = None
        return tokens

    @staticmethod
    def remove_stopwords_and_non_alphabet(tokens):
        '''Remove stopwords and remove all non alphabet characters from string

        Args:
            tokens (_type_): _description_

        Returns:
            _type_: _description_
        '''
        return [word for word in tokens if (not word in STOP_WORDS and word.isalpha())]

    @staticmethod
    def replace_phrases(text):
        '''Replace certain phrases to give better context / sentiment

        Args:
            text (_type_): _description_

        Returns:
            _type_: _description_
        '''
        text = text.replace('"', '')
        text = text.replace("'", '')

        # replace do not with dont so it isn't removed as a stop word
        text = text.replace('do not', 'dont')
        return text

    @staticmethod
    def remove_tickers_mentions_hashtags(text):
        '''Remove tickers / mentions / hashtags from tweets

        Args:
            text (_type_): _description_

        Returns:
            _type_: _description_
        '''
        return re.sub(r'^[$@#]+[A-Za-z][\S]*', '', text, flags=re.MULTILINE).strip()

    @staticmethod
    def remove_links(text):
        '''Remove all http/https links from text

        Args:
            text (_type_): _description_

        Returns:
            _type_: _description_
        '''

        return re.sub(r'(https?:\/\/)(\s)*(www\.)?(\s)*((\w|\s)+\.)*([\w\-\s]+\/)*([\w\-]+)((\?)?[\w\s]*=\s*[\w\%&]*)*', '', text, flags=re.MULTILINE)


def create_vocabulary() -> dict:
    '''_summary_

    Returns:
        dict: _description_
    '''

    vocabulary = {
        # positive words
        "buy": 5,
        "bought": 5,
        "bull": 5,
        "long": 5,
        "support": 5,
        "undervauled": 5,
        "underpriced": 5,
        "cheap": 5,
        "upward": 5,
        "rising": 5,
        "trend": 5,
        "moon": 5,
        "rocket": 5,
        "hold": 5,
        "breakout": 5,
        "call": 5,
        "beat": 5,
        "buying": 5,
        "holding": 5,
        "high": 5,
        "profit": 5,
        "pump": 5,
        "strong": 5,
        "green": 5,
        "invest": 5,
        "spike": 5,
        "incline": 5,

        # negative words
        'sell': -5,
        'bear': -5,
        'bubble': -5,
        'bearish': -5,
        'short': -5,
        'overvalued': -5,
        'overbought': -5,
        'overpriced': -5,
        'expensive': -5,
        'downward': -5,
        'falling': -5,
        'sold': -5,
        'low': -5,
        'put': -5,
        'miss': -5,
        'resistance': -5,
        'squeeze': -5,
        'cover': -5,
        'seller': -5,
        'dump': -5,
        "weak": -5,
        "fail": -5,
        "volatile": -5,
        "destroyed": -5,
        "destroy": -5,
        "tank": -5,
        "tanking": -5,
        "sinking": -5,
        "sink": -5,
        "manipulating": -5,
        "manipulate": -5,
        "red": -5,
        "decline": -5,
    }

    # augment vocabulary db with the same word structure that will be used after it is preprocessed
    new_variations = []
    for key_word, value in vocabulary.items():
        pre_processed_word = Preprocess.clean_text(key_word)
        if pre_processed_word not in vocabulary:
            new_variations.append((pre_processed_word, value))
        new_variations.append(('not_' + key_word, value * -1))
        new_variations.append(('not_' + pre_processed_word, value * -1))
    for variation in new_variations:
        vocabulary[str(variation[0])] = int(variation[1])
    return vocabulary


SENTIMENT_ANALYZER.lexicon.update(create_vocabulary())


def sia_classify(data):
    '''_summary_

    Args:
        data (_type_): _description_

    Returns:
        _type_: _description_
    '''

    score = SENTIMENT_ANALYZER.polarity_scores(data)
    if score["pos"] > score["neg"]:
        return 1
    elif score["neg"] > score["pos"]:
        return -1
    else:
        return 0
