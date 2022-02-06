import random
import sys
import urllib
from urllib.request import urlopen

import pandas as pd
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        # options = Options()
        # options.add_argument('--headless')
        # options.add_argument('--blink-settings=imagesEnabled=false')
        # s = Service(ChromeDriverManager().install())
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        # self.driver = webdriver.Chrome(service=s, options=options)

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
        # req = urllib.request.Request(url, headers=self.random_headers())
        # r = urllib.request.urlopen(url)
        import requests
        r = requests.get(url, headers = self.random_headers()).text
        beautifulsoup = BeautifulSoup(r, features="lxml")
        return beautifulsoup

    def extractArticleInformation(self, url):
        article_dict_list = []
        project_soup = self.get_json_request(url)
        article = project_soup.find_all("section", {"class": "ar-content-left-col"})[0].contents[1]
        try:
            dict = {}
            title = self.extractIssueInformation_Title(article)
            authors = self.extractIssueInformation_Authors(article)
            abstract = self.extractIssueInformation_Abstract(article)
            details = self.extractIssueInformation_details(article)
            dict['Title'] = title
            dict['Authors'] = authors
            dict['Abstract'] = abstract
            dict.update(details)
            article_dict_list.append(dict)
        except:
            pass
        return article_dict_list

    def saveData(self, dict_list):
        path = 'Data/'
        df = pd.DataFrame(dict_list)
        df.to_csv(path + 'LegalIssues.csv')

    def remove_newlines(self, text):
        return text.lstrip().strip()

    def splitString(self, text, sep):
        return text.split(sep)

    def extractIssueInformation_Title(self, child):
        try:
            title = child.find_all("h1")[0].text
            tilte = self.remove_newlines(title)
            return tilte
        except:
            return ""

    def extractIssueInformation_details(self, child):
        details = child.contents[1].find("div", {"class": "article-details"})
        res = dict()
        try:
            journal = details.find("div", {"class": "journal-issue"}).text
            journal = self.remove_newlines(journal)
            res.update({"Journal Title": journal})
            extra = [x.strip() for x in details.contents[3].text.split('\n') if x.strip()]
            res.update({"Link": extra[-1]})
            extra = extra[0]
            vol, pub = extra.split('(')
            pub = " ".join(pub.split(')')[0].split(' ')[3:])
            res.update({"Published Date": pub})
            vol, page = vol.split(":")
            res.update({"Volume": vol, "Pages": page})
            return res
        except:
            return res

    def extractIssueInformation_Authors(self, child):
        authors = child.find("div", {"class": "author"})
        try:
            authors = "".join([x for x in authors.contents[0].contents if isinstance(x, NavigableString)])
            return authors
        except:
            return ""

    def extractIssueInformation_Abstract(self, child):
        abstract = child.find("div", {"class": "abstractSection abstractInFull"})
        try:
            for content in abstract.contents:
                if isinstance(content, Tag):
                    abstract = content.text
                    break
            return abstract
        except:
            return ""

    def getsubIssues(self, url):
        sublinks = []
        project_soup = self.get_json_request(url)
        issues = project_soup.find_all("article", {"class": "teaser"})
        for issue in issues:
            sublinks.append(issue.contents[0].contents[0].contents[0].contents[1].attrs['href'])
        return sublinks

    def getAllIssues(self):
        issueLinks = []
        project_soup = self.get_json_request(self.url)
        issueParents = project_soup.find_all("ul", {"class": "journal-list-pricing"})
        for issueParent in issueParents:
            for issue in issueParent.children:
                if isinstance(issue, Tag):
                    issueLinks.append(issue.contents[0].attrs['href'])
        return issueLinks

    def get_Journal_of_Legal_Analysis(self):
        totalIssueLinks = self.getAllIssues()
        totalSubIssues = []
        final_information_list = []
        for issue in totalIssueLinks:
            totalSubIssues.extend(self.getsubIssues(self.domain + issue))
        for subissue in totalSubIssues:
            information_list = self.extractArticleInformation(self.domain + subissue)
            final_information_list.extend(information_list)
        print(final_information_list)
        df = pd.DataFrame(final_information_list)
        self.saveData(df)


if __name__ == '__main__':
    obj = Scrapping('https://www.annualreviews.org', '/loi/lawsocsci')
    obj.get_Journal_of_Legal_Analysis()
