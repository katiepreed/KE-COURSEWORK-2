
from urllib import response

import requests
from bs4 import BeautifulSoup
import spacy


nlp = spacy.load("en_core_web_sm")
url = "https://www.thecollector.com/25-famous-paintings-curated-masterpieces-in-museums/"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

paragraphs = soup.find_all("p")
captions = soup.find_all("figcaption")

text = " ".join([p.get_text() for p in paragraphs] +
                    [c.get_text() for c in captions])

text = text.replace("\n", " ").strip()

doc = nlp(text)

sentences = [sent.text for sent in doc.sents]

useful_sentences = []
for sent in doc.sents:
    if any(ent.label_ in ["PERSON", "WORK_OF_ART", "DATE"] for ent in sent.ents):
        useful_sentences.append(sent.text)


print("Useful Sentences:")

for sent in useful_sentences:
    print(sent)
