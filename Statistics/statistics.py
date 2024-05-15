import pandas
import numpy as np
import matplotlib.pyplot as plt

from collections import Counter
from dataclasses import dataclass
from wordcloud import WordCloud

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

# Total number of thesis

dataFrame = pandas.read_csv("data.csv", header=0, keep_default_na=False)
allData = dataFrame.apply(lambda row: Thesis(*row), axis=1).tolist()
numberOfEntries = len(allData)
print(f"Összes szakdolgozat száma: {numberOfEntries}")
print("-" * 40)

# Total number of thesis with missing data

missingCount = sum(1 for data in allData if not data.Description or not data.Description)
print(f"Hiányos rekordok száma: {missingCount}")
print("-" * 40)

# Total number of thesis per major

thesisPerMajor = Counter(data.Major for data in allData)
thesisPerMajorSorted = dict(sorted(thesisPerMajor.items(), key=lambda item: item[1], reverse=True))

for key in thesisPerMajorSorted:
    print(f"{key}: {thesisPerMajorSorted[key]}")

# Total number of thesis per department

thesisPerDepartment = Counter(data.Department for data in allData)
thesisPerDepartmentSorted = dict(sorted(thesisPerDepartment.items(), key=lambda item: item[1], reverse=True))
xAxis = list(thesisPerDepartmentSorted.keys())
yAxis = list(thesisPerDepartmentSorted.values())
plt.bar(xAxis, yAxis)
plt.xlabel("Tanszék", weight="bold")
plt.ylabel("Darabszám", weight="bold")
plt.title("Szakdolgozatok száma tanszékenként", weight="bold")
plt.savefig("thesisPerDepartment.png", bbox_inches="tight")
plt.clf()

# Percentage of thesis in faculty

yAxis = list(amount / numberOfEntries for amount in thesisPerDepartmentSorted.values())
plt.pie(yAxis, labels=xAxis, autopct="%.1f%%")
plt.title("A szakdolgozatok százalékos aránya a karon", weight="bold")
plt.tight_layout()
plt.savefig("percentageInFaculty.png", bbox_inches="tight")
plt.clf()

# Change in thesis count with respect to time

thesisPerYear = Counter(data.Year for data in allData)
thesisPerYearSorted = dict(sorted(thesisPerYear.items(), key=lambda item: item[0]))
xAxis = list(thesisPerYearSorted.keys())
yAxis = list(thesisPerYearSorted.values())
plt.xlabel("Év", weight="bold")
plt.xticks(np.arange(xAxis[0], xAxis[-1] + 1, 1))
plt.axhline(y=np.mean(yAxis), color='red', linestyle='--', linewidth=3, label='Átlag')
plt.legend()
plt.plot(xAxis, yAxis, marker="o")
plt.ylabel("Darabszám", weight="bold")
plt.title("A szakdolgozatok számának időbeli változása", weight="bold")
plt.tight_layout()
plt.savefig("thesisPerYear.png", bbox_inches="tight")
plt.clf()

# Word cloud from topic tags

dataWithoutEmptyRecords = list(filter(lambda row: row.Description or row.Tags, allData))
topics = []

for record in dataWithoutEmptyRecords:
    tags = record.Tags.split(", ")
    topics.extend(tags)

text = ' '.join(topics)
wordCloud = WordCloud(width=800, height=400, background_color="white").generate(text)
plt.imshow(wordCloud, interpolation="bilinear")
plt.axis("off")
plt.savefig("wordCloud.png", bbox_inches="tight")
plt.clf()