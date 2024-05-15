import pandas
import bar_chart_race as bcr

from collections import defaultdict
from dataclasses import dataclass

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

dataFrame = pandas.read_csv("data.csv", header=0, keep_default_na=False)
allData = dataFrame.apply(lambda row: Thesis(*row), axis=1).tolist()
dataWithoutEmptyRecords = list(filter(lambda row: row.Description or row.Tags, allData))

years = sorted(set(int(data.Year) for data in dataWithoutEmptyRecords))
formattedDictionary = dict.fromkeys(years)

for year in years:
    tagCount = defaultdict(int)
    dataPerYear = list(filter(lambda row: int(row.Year) == year, dataWithoutEmptyRecords))

    for row in dataPerYear:
        
        for tag in row.Tags.split(", "):
            tagCount[tag] += 1

    formattedDictionary[year] = dict(sorted(tagCount.items(), key=lambda item: item[1]))

dataFrame = pandas.DataFrame.from_dict(formattedDictionary, orient="index")
dataFrame.fillna(0, inplace=True)
dataFrame.sort_index(inplace=True)

bcr.bar_chart_race(
    df=dataFrame,
    filename="barChartRaceAbsolute.mp4",
    n_bars=10,
    end_period_pause=3000,
    filter_column_colors=True
)