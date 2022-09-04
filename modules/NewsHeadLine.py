from logging import getLogger
from modules.Models import sia_classify, Preprocess
from bs4 import BeautifulSoup as soup
from selenium import webdriver
import os
import time
import datetime
Logger = getLogger(__name__)


def convert24(str1):
    '''_summary_

    Args:
        str1 (_type_): _description_

    Returns:
        _type_: _description_
    '''

    # Checking if last two elements of time
    # is AM and first two elements are 12
    if str1[-2:] == "AM" and str1[:2] == "12":
        return "00" + str1[2:-2]

    # remove the AM
    elif str1[-2:] == "AM":
        return str1[:-2]

    # Checking if last two elements of time
    # is PM and first two elements are 12
    elif str1[-2:] == "PM" and str1[:2] == "12":
        return str1[:-2]

    else:

        # add 12 to hours and remove PM
        return str(int(str1[:2]) + 12) + str1[2:8]


class NewsHeadLine:
    '''_summary_
    '''

    def __init__(self, populate_db, model=None, ticker=None):
        '''News headline scraper

        Args:
            ticker (_type_): _description_
        '''
        self.ticker = ticker
        self.headlines = []
        self.populate_db = populate_db
        self.model = model
        options = webdriver.ChromeOptions()
        # options.add_argument("--incognito")
        options.add_argument("disable-gpu")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')

        self.driver = webdriver.Chrome(
            executable_path=os.getcwd()+"/input/chromedriver.exe", options=options)
        self.driver.implicitly_wait(5)

    def scrape_sites(self):
        '''_summary_
        '''
        scraper = [self.scrape_finviz, self.scrape_cnbc]

        for scrape in scraper:
            try:
                scrape()
            except Exception as err:
                Logger.exception(err)

    def close(self) -> None:
        '''_summary_
        '''
        self.driver.quit()

    def scrape_cnbc(self):
        '''_summary_
        '''
        self.driver.get(
            f"https://www.cnbc.com/quotes/{self.ticker.upper()}?tab=news")
        Logger.debug("Waiting 10 seconds for website to fully load!")
        time.sleep(10)

        for b in range(2):
            try:
                Logger.debug("Expanding news section...")
                self.driver.find_element_by_css_selector(
                    'div.undefined:nth-child(1) > button:nth-child(3)').click()
            except Exception as err:
                Logger.exception(err)
                break

        cnbc_news_links = set()
        for element in self.driver.find_elements_by_class_name("LatestNews-headline"):
            cnbc_link = str(element.get_attribute("href"))
            if cnbc_link.startswith("https://www.cnbc.com/"):
                cnbc_news_links.add(cnbc_link)

        scraped_link_counter = 0
        for cnbc_link in cnbc_news_links:
            Logger.debug('visiting site %s', cnbc_link)
            self.driver.get(cnbc_link)
            headline_content = None

            for i in range(2):
                try:
                    date_ = self.driver.find_element_by_css_selector(
                        '.ArticleHeader-time > time:nth-child(1)').get_attribute('datetime')
                    date_ = date_.split("T")
                    date_stamp = date_[0]
                    time_stamp = date_[1].split("+")[0]
                    headline_content = {
                        "ID": hash(self.driver.title),
                        "Ticker": self.ticker,
                        "Date": (date_stamp + " " + time_stamp).strip(),
                        "Text": self.driver.title,
                    }
                    break
                except Exception as err:
                    Logger.exception(err)
                    self.driver.refresh()
            if headline_content is None:
                continue
            cleaned_headline = Preprocess.clean_text(headline_content['Text'])
            if self.populate_db:
                headline_content["Sentiment"] = sia_classify(
                    cleaned_headline)
            else:
                headline_content["Sentiment"] = self.model.classify(
                    cleaned_headline)
            Logger.debug("Headline scraped %s", headline_content)
            self.headlines.append(headline_content)
            scraped_link_counter += 1
        Logger.debug("Successfully scraped %s from cbnc for ticker %s",
                     scraped_link_counter,
                     self.ticker)

    def scrape_finviz(self):
        '''_summary_'''
        self.driver.get(
            f"http://finviz.com/quote.ashx?t={self.ticker.lower()}")
        Logger.debug("Waiting 10 seconds for website to fully load!")
        time.sleep(10)

        news_table = soup(self.driver.page_source, "html.parser").select_one(
            'html body.yellow-tooltip div.content div.fv-container table tbody tr td table tbody tr td table#news-table.fullview-news-outer')
        date = None
        scraped_link_counter = 0
        for row in news_table.findAll('tr'):
            try:
                title = row.a.text.strip()
                source = row.span.text.strip()
                posted_at = row.td.text.split(' ')
                if len(posted_at) > 1:
                    date = posted_at[0].split("-")
                    timestamp = posted_at[1].strip()
                else:
                    timestamp = posted_at[0].strip()

                timestamp.replace('\xa0\xa0', '')
                date_time_stamp = f'20{date[2]}-{datetime.datetime.strptime(date[0], "%b").month}-{date[1]} {convert24(timestamp[:-2] + ":00 " + timestamp[-2:])}'
                headline_content = {
                    "ID": hash(title),
                    "Ticker": self.ticker.upper(),
                    "Date": date_time_stamp.strip(),
                    "Text": title,
                }
                cleaned_headline = Preprocess.clean_text(
                    headline_content['Text'])
                if self.populate_db:
                    headline_content["Sentiment"] = sia_classify(
                        cleaned_headline)
                else:
                    headline_content["Sentiment"] = self.model.classify(
                        cleaned_headline)

                Logger.debug("Headline scraped %s", headline_content)
                self.headlines.append(headline_content)
                scraped_link_counter += 1
            except Exception as err:
                Logger.warning(err)
                continue
        Logger.debug("Successfully scraped %s from finviz for ticker %s",
                     scraped_link_counter,
                     self.ticker)
