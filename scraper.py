from modules.Twitter import Twitter
import logging
import coloredlogs
import time
import os
from modules.Models import *
from modules.NewsHeadLine import NewsHeadLine

logging.basicConfig(filename=f'{os.getcwd()}/output/logs/{time.strftime("%m-%d-%Y %I-%M%p")}.log',
                    encoding='utf-8',
                    level=logging.WARNING,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
coloredlogs.install(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level="debug")


def clean_before_save(data):
    data = data.replace(';', '')
    data = data.replace('\n', '').strip()
    return data


def validate_doesnt_exist(data):
    with open(os.getcwd() + "/input/training_data.csv", encoding='utf-8', mode='r') as file_reader:
        for line in file_reader.readlines():
            if str(data["ID"]) == str(line.split(";")[0]):
                logging.warning("Data point already exists so not saving!")
                return True
    return False


def dict_to_str(data_dict: dict):
    return f'{data_dict["ID"]};{data_dict["Ticker"]};{data_dict["Date"]};{data_dict["Text"]};{data_dict["Sentiment"]}'


def save_data(data):
    with open(os.getcwd() + "/input/training_data.csv", encoding='utf-8', mode='a+') as file_writer:
        if isinstance(data, list):
            for datapoint in data:
                if validate_doesnt_exist(datapoint):
                    continue
                datapoint["Text"] = clean_before_save(datapoint["Text"])
                file_writer.write(f'{dict_to_str(datapoint)}\n')
        if not validate_doesnt_exist(datapoint):
            datapoint["Text"] = clean_before_save(datapoint["Text"])
            file_writer.write(f'{dict_to_str(datapoint)}\n')


def start_scraping(populate_db_):
    twitter = Twitter(populate_db=populate_db_)
    newsheadline = NewsHeadLine(populate_db=populate_db_)
    for ticker in TICKERS:
        logging.debug("Scraping tweets for ticker %s", ticker)
        tweets = twitter.fetch_tweets_and_classify(ticker=ticker)
        save_data(tweets)

        logging.debug("Scraping headlines for ticker %s", ticker)
        newsheadline.ticker = ticker
        newsheadline.headlines.clear()
        newsheadline.scrape_sites()
        save_data(newsheadline.headlines)
    newsheadline.close()


if __name__ == "__main__":
    start_scraping(True)
