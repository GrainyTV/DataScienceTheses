import os
import pandas
import re
import requests
import sys

from dataclasses import dataclass
from dataclasses import fields
from lxml import html
from lxml.html import HtmlElement

@dataclass
class Thesis:
    Title: str
    Teacher: str
    Student: str
    Year: int
    Department: str
    Level: str
    Major: str
    Tags: str
    Description: str

def attributeOf(html: HtmlElement, attribute: str) -> str:
    assert attribute in html.attrib, f"Attribute '{attribute}' does not exist in the HTML node"
    return html.get(attribute)

def contentOf(html: HtmlElement) -> str:
    content = html.text
    assert content is not None, "The provided HTML node is empty"
    return content

def oneOrMoreHtmlNodeByCss(html: HtmlElement, selector: str) -> list[HtmlElement]:
    nodes = html.cssselect(selector)
    assert len(nodes) >= 1, "Expected one or more HTML nodes, but none were found"
    return nodes

def oneHtmlNodeByCss(html: HtmlElement, selector: str) -> HtmlElement:
    node = html.cssselect(selector)
    assert len(node) == 1, "Expected one HTML node, but either none or multiple were found"
    return node[0]

def scrapeWebsite(url: str) -> HtmlElement:
    response = requests.get(url)
    website = html.fromstring(response.content)
    return website

def howManyPages(html: HtmlElement) -> list[int]:
    if len(html.cssselect('ul.pager')) == 0:
        return range(1, 1 + 1)
    
    noPagesDiv = oneHtmlNodeByCss(html, 'ul.pager')
    lastPageIdx = contentOf(oneOrMoreHtmlNodeByCss(noPagesDiv, 'a')[-1])
    return range(1, int(lastPageIdx) + 1)

def extractYear(seasonInfo: str) -> int:
    firstYear = re.compile(r'(?<= )\d+(?=-)').search(seasonInfo).group()
    secondYear = re.compile(r'(?<=-)\d+(?=.)').search(seasonInfo).group()
    season = re.compile(r'(?:tavasz|ősz)').search(seasonInfo).group()
    return int(secondYear) if season == 'tavasz' else int(firstYear)

def extractMajor(seasonInfo: str) -> str:
    pattern = re.compile(r'(?<=, ).*(?=,)')
    match = pattern.search(seasonInfo)
    return match.group()

def haveAllFromThisBatch(html: HtmlElement, amount: int) -> bool:
    divWithAmount = contentOf(oneHtmlNodeByCss(html, 'div#main > p:last-of-type'))
    batch = re.compile(r'\d+').search(divWithAmount).group()
    return True if int(batch) == amount else False

def reportProgress(iteration: int, total: int, department: str, level: str, barLength: int = 32) -> None:
    percent = int((iteration / total) * 100)
    progress = int((iteration / total) * barLength)
    bar = '#' * progress + '-' * (barLength - progress)
    sys.stdout.write("\r" + " " * 100 + "\r")
    sys.stdout.write(f'\r{department},{level}: [{bar}] {percent}%')
    sys.stdout.flush()

# ============================== #
# Entry point of the application #
# ============================== #

fileName = "data.csv"
baseUrl = "http://diplomaterv.vik.bme.hu"
departments = [ "AUT", "EET", "ETT", "HIT", "HVT", "IIT", "MIT", "SZIT", "TMIT", "VET" ]
levels = [ "BSc", "FiveGrade" ]
header = [ field.name for field in fields(Thesis) ]
dataFrame = None

if os.path.exists(fileName):
    dataFrame = pandas.read_csv(fileName, header=0, keep_default_na=False)

else:
    dataFrame = pandas.DataFrame(columns=header)
    dataFrame.to_csv(fileName, index=False)

allData = dataFrame.apply(lambda row: Thesis(*row), axis=1).tolist()

for department in departments:

    for level in levels:

        currentData = list(filter(lambda thesis: thesis.Department == department and thesis.Level == level, allData))
        thesesBatchSite = scrapeWebsite(f"{baseUrl}/hu/Browse.aspx?d={department}&p={level}&Page={1}")

        if haveAllFromThisBatch(thesesBatchSite, len(currentData)):
            reportProgress(1, 1, department, level)
            continue

        pages = howManyPages(thesesBatchSite)

        for page in pages:

            reportProgress(page, len(pages), department, level)

            if page > 1:
                thesesBatchSite = scrapeWebsite(f"{baseUrl}/hu/Browse.aspx?d={department}&p={level}&Page={page}")
            
            entries = []

            for thesis in oneOrMoreHtmlNodeByCss(thesesBatchSite, 'div.result'):

                title = contentOf(oneHtmlNodeByCss(thesis, 'h3 > a'))
                student = contentOf(oneHtmlNodeByCss(thesis, 'a.hlStudent'))

                if len(currentData) > 0 and any(data.Title == title and data.Student == student for data in currentData):
                    continue

                teacher = contentOf(oneHtmlNodeByCss(thesis, 'a.hlSupervisor'))
                extraInfo = ' '.join(contentOf(oneHtmlNodeByCss(thesis, 'span.meta')).split())
                year = extractYear(extraInfo)
                major = extractMajor(extraInfo)

                detailsPageUrl = f"{baseUrl}{attributeOf(oneOrMoreHtmlNodeByCss(thesis, 'a')[0], 'href')}"
                detailsPage = scrapeWebsite(detailsPageUrl)
                
                tags = attributeOf(oneHtmlNodeByCss(detailsPage, 'meta[itemprop="keywords"]'), 'content')
                description = ' '.join(contentOf(paragraph).strip() for paragraph in oneOrMoreHtmlNodeByCss(detailsPage, 'div.clear.abstract > p:not(:empty)'))

                entry = Thesis(title, teacher, student, year, department, level, major, tags, description)
                entries.append(entry)

            if len(entries) > 0:
                neededDataFrame = pandas.DataFrame([entry.__dict__ for entry in entries], columns=header)
                neededDataFrame.to_csv(fileName, header=False, mode='a', index=False)