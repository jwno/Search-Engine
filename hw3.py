from collections import defaultdict
from bs4 import BeautifulSoup
import re
import traceback
import json
import math

SPECIAL_TAG_FACTORS = {
    "strong": 1.2,
    "b": 1.2,
    "bold": 1.2,
    "h1": 1.4,
    "h2": 1.3,
    "h3": 1.25,
    "title": 1.5,
}

class Posting:
    def __init__(self):
        self.tf = 0
        self.special_tags = set()

class Data:
    def __init__(self):
        self.idf = 0
        self.postings = defaultdict(Posting)

class InvertedIndex:
    def __init__(self):
        self.dictionary = defaultdict(Data)
        self.num_doc_ids = 0
    def __getitem__(self, term):
        return self.dictionary[term]
    def __setitem__(self, term, data):
        self.dictionary[term] = data
    def get_number_of_terms(self):
        return len(self.dictionary.keys())
    def items(self):
        return self.dictionary.items()
    def get_json(self, outfile):
        j = dict()
        for term, data in self.dictionary.items():
            j[term] = dict()
            j[term]["idf"] = data.idf
            j[term]["postings"] = dict()
            for docID, posting in data.postings.items():
                j[term]["postings"][docID] = dict()
                j[term]["postings"][docID]["tf"] = posting.tf
                j[term]["postings"][docID]["special_tags"] = list(posting.special_tags)
        json.dump(j, outfile, indent = 4)

def tokenize(webpage, docID):
    global index
    soup = BeautifulSoup(webpage, 'lxml')
    text = soup.get_text()
    tokens = re.split('\W+', text.lower().strip())
    for token in tokens:
        if token != "":
            index[token].postings[docID].tf += 1

    special_tags = soup.find_all(["strong", "b", "bold", "h1", "h2", "h3", "title"])
    for special_tag in special_tags:
        special_tag_content = special_tag.get_text().strip()
        tokens = re.split('\W+', special_tag_content)
        for token in tokens:
            if token != "":
                index[token].postings[docID].special_tags.add(special_tag.name)

def get_results(query):
    #maps docID to its score for the query
    global record_data
    score = defaultdict(float)
    for token in query.split(" "):
        for docID, posting in index[token].postings.items():
            constant_factor = 1
            for special_tag in posting.special_tags:
                constant_factor *= SPECIAL_TAG_FACTORS[special_tag]
            score[docID] += constant_factor * (1 + math.log(posting.tf) * math.log(index[token].idf))
    sorted_keys = sorted(score.keys(), reverse=True, key=lambda k : score[k])
    results = []
    for key in sorted_keys:
        results.append(record_data[key])
    return results

index = InvertedIndex();
with open("/home/trenton/CS121/HW4/WEBPAGES_CLEAN/bookkeeping.json") as book_data:
        record_data = json.load(book_data)
try:
    for docID in list(list(record_data.keys())):
        index.num_doc_ids += 1
        with open("/home/trenton/CS121/HW4/WEBPAGES_CLEAN/" + docID) as webpage:
            tokenize(webpage, docID)
    for term, data in index.items():
        data.idf = index.num_doc_ids/float(len(data.postings))
except:
    traceback.print_exc()


