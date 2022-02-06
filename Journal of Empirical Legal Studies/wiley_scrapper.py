import random
import sys

import pandas as pd
from bs4 import BeautifulSoup, Tag, NavigableString

sys.setrecursionlimit(200000)

desktop_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']


class Scrapping:

    def __init__(self, website_url, suburl):
        self.domain = website_url
        self.url = self.domain + suburl
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

    def random_headers(self):
        return {'User-Agent': random.choice(desktop_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "referrer": "https://www.annualreviews.org/",
                "referrerPolicy": "origin",
                "method": "GET",
                "accept-language": "en-US,en;q=0.9,te;q=0.8",
                "cache-control": "max-age=0",
                "mode": "cors",
                "credentials": "include"}

    def get_json_request(self, url):
        import time
        time.sleep(2)
        import requests
        r = requests.get(url, headers=self.random_headers()).text
        beautifulsoup = BeautifulSoup(r, features="lxml")
        return beautifulsoup

    def extractArticleInformation(self, url):
        link = self.domain + url
        article = self.get_json_request(link)
        article_dict = dict()
        try:
            title = self.extractIssueInformation_Title(article)
            authors = self.extractIssueInformation_Authors(article)
            abstract = self.extractIssueInformation_Abstract(article)
            details = self.extractIssueInformation_details(article)
            article_dict['Title'] = title
            article_dict['Authors'] = authors
            article_dict['Abstract'] = abstract
            article_dict['Published Date'] = article.find("span", {"class": "epub-date"}).text
            article_dict.update(details)
            article_dict['Link'] = link
        except:
            pass
        return article_dict

    def saveData(self, dict_list):
        path = 'Data/'
        df = pd.DataFrame(dict_list)
        df.to_csv(path + 'EmpiricalLegalStudies.csv')

    def remove_newlines(self, text):
        return text.lstrip().strip()

    def splitString(self, text, sep):
        return text.split(sep)

    def extractIssueInformation_Title(self, child):
        try:
            title = child.find_all("h1", {"class": "citation__title"})[0].text
            tilte = self.remove_newlines(title)
            return tilte
        except:
            return ""

    def extractIssueInformation_details(self, child):
        details = child.contents[1].find("div", {"class": "article-row-right"})
        res = dict()
        try:
            journal = "Journal of Empirical Legal Studies"
            res.update({"Journal Title": journal})

            issue = details.find("div", {"class": "extra-info-wrapper cover-image__details"})
            issue_details = issue.find("p", {"class": "volume-issue"})
            if not issue_details:
                issue_details = "Early View"
            else:
                issue_details = issue_details.contents[0].attrs["title"][5:]
            pages = issue.find("p", {"class": "page-range"})
            if not pages:
                pages = "NA"
            else:
                pages = pages.contents[1].text
            res.update({"Volume": issue_details, "Pages": pages})
            return res
        except:
            return res

    def extractIssueInformation_Authors(self, child):
        authors_section = child.find("div", {"class": "loa-wrapper loa-authors hidden-xs desktop-authors"})
        try:
            authors = authors_section.find_all("p", {"class": "author-name"})
            return ", ".join([author.contents[0] for author in authors])
        except:
            return ""

    def extractIssueInformation_Abstract(self, child):
        abstract_section = child.find("section", {"class": "article-section article-section__abstract"})
        try:
            abstract = abstract_section.find("p")
            abstract = abstract.text
            return abstract
        except:
            return ""

    def getArticleDetails(self, soup):
        articles = soup.find("ul", {"class": "rlist search-result__body items-results"})
        if not articles:
            return []
        details = []
        articles = [x for x in articles.contents if isinstance(x, Tag)]
        for article in articles:
            url = article.find("a", {"class": "publication_title visitable"}).attrs['href']
            details.append(self.extractArticleInformation(url))
        return details

    def getNextPageUrl(self, soup):
        next_link = soup.find("a", {"class": "pagination__btn--next"})
        if next_link:
            url = next_link.attrs["href"]
            return url
        else:
            return None

    def get_Journal_of_Legal_Analysis(self):
        final_information_list = []
        while True:
            soup = self.get_json_request(self.url)
            final_information_list.extend(self.getArticleDetails(soup))
            url = self.getNextPageUrl(soup)
            if not url:
                break
            else:
                self.url = url
        print(final_information_list)
        df = pd.DataFrame(final_information_list)
        self.saveData(df)


if __name__ == '__main__':
    obj = Scrapping('https://onlinelibrary.wiley.com', '/action/doSearch?SeriesKey=17401461&sortBy=Earliest')
    obj.get_Journal_of_Legal_Analysis()
