import nltk
import os
import pandas
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

from collections import Counter
from dataclasses import dataclass
from gensim.models import Word2Vec
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.decomposition import IncrementalPCA
from sklearn.manifold import TSNE

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

def mostFrequent(List, n):
    occurence_count = Counter(List)
    return [item for item, _ in occurence_count.most_common(n)]

dataFrame = pandas.read_csv("data.csv", header=0, keep_default_na=False)
allData = dataFrame.apply(lambda row: Thesis(*row), axis=1).tolist()
dataWithoutEmptyRecords = list(filter(lambda row: row.Description or row.Tags, allData))

nltk.download(info_or_id="stopwords", download_dir=f"{os.getcwd()}/venv/nltk_data", quiet=True)
nltk.download(info_or_id="punkt", download_dir=f"{os.getcwd()}/venv/nltk_data", quiet=True)
descriptionTopics = []
unnecessaryWords = set(stopwords.words("hungarian"))

for record in dataWithoutEmptyRecords: 
    tokens = word_tokenize(record.Description.lower())
    descriptionTopics.append([word for word in tokens if word not in unnecessaryWords])

mostFrequentTopics = []
numberOfTagsPerDepartment = 5
numberOfSimilarTagsPerDepartment = 5
departments = sorted(set([data.Department for data in dataWithoutEmptyRecords]))

for department in departments:
    tags = []

    for record in [data for data in dataWithoutEmptyRecords if data.Department == department]:
        tags.extend(record.Tags.lower().split(", "))

    mostFrequentTopics.append(mostFrequent(tags, numberOfTagsPerDepartment))
    tags.clear()

model = Word2Vec(sentences=descriptionTopics, vector_size=100, min_count=20, workers=4, seed=0)
wv = model.wv

neededVectors = []
neededLabels = []
numberOfDepartments = len(mostFrequentTopics)
colors = list(zip(cm.rainbow(np.linspace(0, 1, numberOfDepartments)), departments))
indices = [0 for i in range(numberOfDepartments)]

for idx, topicsPerDepartment in enumerate(mostFrequentTopics):
    for topic in topicsPerDepartment:
        try:
            for similar in wv.most_similar(positive=topic, topn=numberOfSimilarTagsPerDepartment):
                neededVectors.append(wv[similar[0]])
                neededLabels.append(similar[0])
                indices[idx] += 1
                print(f"{topic}: {similar[0]}")
        except KeyError:
            pass

vectors = np.asarray(neededVectors)
labels = np.asarray(neededLabels)
tsne = TSNE(n_components=2, random_state=0)
vectors = tsne.fit_transform(vectors)

x = [v[0] for v in vectors]
y = [v[1] for v in vectors]

start = 0
for batch in range(len(colors)):
    color = colors[batch][0]
    label = colors[batch][1]
    count = indices[batch]
    end = start + count

    for i in range(start, end):
        plt.scatter(x[i], y[i], color=color, label=label if i == start else "")

    start = end

plt.title("A tanszékek leggyakoribb címkéihez legközelelebbi elemek", weight="bold")
plt.legend(loc="center right", bbox_to_anchor=(1.2, 0.5), ncol=1, fancybox=True, shadow=True)
plt.savefig("embedding.png", bbox_inches="tight")
plt.clf()