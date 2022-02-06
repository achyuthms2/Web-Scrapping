from bs4 import BeautifulSoup
import urllib
import sys
import random
from urllib.request import urlopen
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os

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

    def __init__(self, website_url):
        self.url = website_url
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--blink-settings=imagesEnabled=false')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    def random_headers(self):
        return {'User-Agent': random.choice(desktop_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

    def get_json_request(self, url):
        req = urllib.request.Request(url, headers=self.random_headers())
        r = urllib.request.urlopen(req)
        beautifulsoup = BeautifulSoup(r, "lxml")
        return beautifulsoup

    def extractIssueInformation(self, url):
        issueDict_list = []
        project_soup = self.get_json_request(url)
        issues = project_soup.find_all("div", {"class": "al-article-list-group"})
        if len(issues) == 0:
            issues = project_soup.find_all("div", {"class": "section-container"})
        for issue in issues:
            for child in issue.children:
                try:
                    articles = child.find_all('div', {'class': 'al-article-items'})
                    for article in articles:
                        try:
                            dict = {}
                            title = self.extractIssueInformation_Title(article)
                            authors = self.extractIssueInformation_Authors(article)
                            citation = self.extractIssueInformation_citation(article)
                            abstract = self.getAbstract(citation['Link'])
                            published_date = self.getPublication_date(citation['Link'])
                            dict['Title'] = title
                            dict['Authors'] = authors
                            dict['Abstract'] = abstract
                            dict['Published Date'] = published_date
                            dict.update(citation)
                            issueDict_list.append(dict)
                        except:
                            continue
                except:
                    continue
        return issueDict_list

    def saveData(self, dict_list):
        path = 'Data/'
        df = pd.DataFrame(dict_list)
        df.to_csv(path + '/LegalIssues.csv')

    def remove_newlines(self, text):
        return text.strip()

    def splitString(self, text, sep):
        return text.split(sep)

    def extractIssueInformation_Title(self, child):
        try:
            title = child.find_all("h5", {"class": 'customLink item-title'})[0].text
            tilte = self.remove_newlines(title)
            return tilte
        except:
            return ""

    def extractCitationDict(self, citation_list):
        dict = {}
        dict["Journal Title"] = citation_list[0]
        dict["Volume"] = citation_list[1]
        if "Issue" in citation_list[2]:
            dict["Issue"] = citation_list[2]
            dict["Year"] = citation_list[3]
            dict["Pages"] = citation_list[4]
            dict["Link"] = citation_list[5]
        else:
            dict["Issue"] = ""
            dict["Year"] = citation_list[2]
            dict["Pages"] = citation_list[3]
            dict["Link"] = citation_list[4]
        return dict

    def extractIssueInformation_Authors(self, child):
        authors = child.find_all("div", {"class": 'al-authors-list'})
        try:
           author = self.remove_newlines(authors[0].text)
           authorlist = self.splitString(author, ",")
           return authorlist
        except:
            return []

    def extractIssueInformation_citation(self, child):
        try:
            authors = child.find_all("div", {"class": 'ww-citation-primary'})
            author = self.remove_newlines(authors[0].text)
            citation_list = self.splitString(author, ",")
            citation_dict = self.extractCitationDict(citation_list)
            return citation_dict
        except:
            return []

    def getissueIdentifer(self, url):
        project_soup = self.get_json_request(url)
        identifier = project_soup.find_all("h1", {"class": "issue-identifier"})
        return identifier.text

    def getAbstract(self, url):
        self.driver.get(url)
        abstarct_ele = self.driver.find_element_by_class_name("abstract")
        try:
            return abstarct_ele.text
        except:
            return ""

    def getPublication_date(self, url):
        self.driver.get(url)
        publication_ele = self.driver.find_element_by_class_name("ww-citation-date-wrap")
        try:
            publication_date = self.splitString(publication_ele.text, ":")
            return publication_date[1]
        except:
            return ""

    def getsubIssues(self, url):
        sublinks = []
        project_soup = self.get_json_request(url)
        issues = project_soup.find_all("div", {"class": "single-dropdown-wrap dropdown-issue"})
        totalIssues = issues[0].find_all('option')
        for issueLink in totalIssues:
            sublinks.append(issueLink.attrs['value'])
        return sublinks

    def getMainIssuelink(self):
        issueLink = []
        years_link = []
        project_soup = self.get_json_request(self.url)
        issues = project_soup.find_all("div", {"class": "single-dropdown-wrap dropdown-year"})
        for issue in issues[0].children:
            try:
                totalIssues = issue.find_all('option')
                for link in totalIssues:
                    issueLink.append(link.attrs['value'])
                    years_link.append(link.text)
                return issueLink, years_link
            except:
                print("No isssues")

    def prepareCSV(self, file_path):
        df = pd.read_csv(file_path, index_col=0)
        index_list = [2021]
        rows = df.shape[0]
        for i in range(1, rows):
            index_list.append(2021-i)
        df[df.columns[0]] = index_list
        df.columns = ["Year", "subissueLink1", "subissueLink2", "subissueLink3", "subissueLink4"]
        df.to_csv(file_path)

    def get_finalInformation(self, file_path):
        df = pd.read_csv(file_path, index_col=0)
        year_list = df['Year'].values.tolist()
        df.set_index('Year', inplace = True)
        subissues_list = df.values.tolist()
        for year, subissues in zip(year_list, subissues_list):
            for index, subissue in enumerate(subissues):
                if self.isFileexists(year, index):
                    continue
                print(year)
                print(subissue)
                information_list = self.extractIssueInformation('https://academic.oup.com/' + subissue)
                print(len(information_list))
                if len(information_list) > 0:
                    df = pd.DataFrame(information_list)
                    df.to_csv('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/' + str(year) + '_' + str(index) + '.csv')


    def isFileexists(self, year, index):
        files = os.listdir('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/')
        if (str(year) + '_' + str(index) + '.csv') in files:
            return True
        return False

    def get_Journal_of_Legal_Analysis(self):
        totalIssueLinks = self.getMainIssuelink()
        df = pd.DataFrame(totalIssueLinks)
        df.to_csv('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/' + 'Acedemic_MainIssueLinks.csv')
        issueLinks = totalIssueLinks[0]
        totalSubIssues = []
        final_information_list = []
        for subIssue in issueLinks:
            totalSubIssues.append(self.getsubIssues('https://academic.oup.com/' + subIssue))
        df = pd.DataFrame(totalSubIssues)
        df.to_csv('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/' + 'Acedemic_subissues.csv')
        self.get_finalInformation('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/Acedemic_subissues.csv')
        for subissues in totalSubIssues:
            for subissue in subissues:
                information_list = self.extractIssueInformation('https://academic.oup.com/' + subissue)
                final_information_list.extend(information_list)
        df = pd.DataFrame(final_information_list)
        self.saveData(df)

if __name__ == '__main__':
    obj = Scrapping('https://academic.oup.com/jiel/issue')
    #obj.get_Journal_of_Legal_Analysis()
    obj.get_finalInformation('/Users/bhanugollapudi/Documents/Ding_Proj/ProjectManagementSoftware/Data/Acedemic_subissues.csv')