"""
Requirements: python -m spacy download en_core_web_sm
"""

import requests
from bs4 import BeautifulSoup
import spacy
import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from rdflib import Literal, Namespace

MYONT  = Namespace("https://ontologeez/")
SCHEMA = Namespace("https://schema.org/")

RELATION_MAP = {
    "creator": MYONT.createdBy,
    "author": MYONT.createdBy,
    "painter": MYONT.createdBy,
    "movement": MYONT.hasPeriod,
    "style": MYONT.hasPeriod,
    "genre": MYONT.hasTheme,
    "main subject": MYONT.hasTheme,
    "depicts": MYONT.hasTheme,
    "inception": SCHEMA.dateCreated,
    "point in time": SCHEMA.dateCreated,
    "date of production": SCHEMA.dateCreated,
    "location": MYONT.displayedBy,
    "exhibited at": MYONT.displayedBy,
    "subsidiary": MYONT.displayedBy,
    "collection": MYONT.displayedBy,
}

# Properties where the object should be a literal, not a URI
LITERAL_PROPERTIES = {SCHEMA.dateCreated, MYONT.hasPeriod}


def make_uri(label):
    """
    Create a new URI for an entity that does not exist in the graph.
    """
    safe = re.sub(r"[^a-zA-Z0-9 ]", "", label).strip().replace(" ", "_")
    return MYONT[safe] if safe else None


def resolve_uri(label, g):
    """
    This function takes a label and tries to find if the entity already
    exists in the graph. If found, returns the existing URI.
    Otherwise, mints a new URI.
    """
    label_lower = label.lower().strip()

    for s, _, o in g.triples((None, SCHEMA.name, None)):
        if str(o).lower() == label_lower:
            return s

    return make_uri(label)


def parse_generated_text(rebel_output_text):
    """
    REBEL outputs special tokens like:
    <triplet> subject <subj> object <obj> relation

    This function converts that into a list of
    {head, type, tail} dictionaries.
    """
    extracted_triples = []
    current_subject = ""
    current_object = ""
    current_relation = ""
    parsing_state = None

    tokens = rebel_output_text.replace("<s>", "").replace("</s>", "").split()

    for token in tokens:
        if token == "<triplet>":
            if current_subject and current_relation and current_object:
                extracted_triples.append({
                    "head": current_subject.strip(),
                    "type": current_relation.strip(),
                    "tail": current_object.strip()
                })
            current_subject = ""
            current_object = ""
            current_relation = ""
            parsing_state = "subject"
        elif token == "<subj>":
            parsing_state = "object"
        elif token == "<obj>":
            parsing_state = "relation"
        else:
            if parsing_state == "subject":
                current_subject += " " + token
            elif parsing_state == "object":
                current_object += " " + token
            elif parsing_state == "relation":
                current_relation += " " + token

    if current_subject and current_relation and current_object:
        extracted_triples.append({
            "head": current_subject.strip(),
            "type": current_relation.strip(),
            "tail": current_object.strip()
        })

    return extracted_triples


def extract_sentence_triples(sentence_text, spacy_entities, tokenizer, model):
    """
    Given a sentence and its spaCy entities, use REBEL to extract triples
    and map them to ontology predicates.
    """
    tokenized_input = tokenizer(sentence_text, return_tensors="pt")

    generated_output_tokens = model.generate(
        **tokenized_input,
        max_new_tokens=128,
        num_beams=3,
        early_stopping=True,
    )

    decoded_output_text = tokenizer.batch_decode(generated_output_tokens, skip_special_tokens=False)[0]
    output_triples = parse_generated_text(decoded_output_text)

    # Extract detected artwork names for subject identification
    detected_artworks = [ent.text for ent in spacy_entities if ent.label_ == "WORK_OF_ART"]

    # Lowercase entity list for fuzzy matching
    list_of_entities = [ent.text.lower().strip() for ent in spacy_entities]

    results = []

    for triple in output_triples:
        raw_relation = triple["type"].lower()
        mapped = RELATION_MAP.get(raw_relation)

        if not mapped:
            continue

        subj_raw = triple["head"]
        obj_raw = triple["tail"]

        match_found = any(
            ent in subj_raw.lower() or subj_raw.lower() in ent or
            ent in obj_raw.lower() or obj_raw.lower() in ent
            for ent in list_of_entities
        )

        if not match_found:
            continue

        subj_clean = subj_raw.replace("\u2019s", "").replace("'s", "").strip()
        obj_clean = obj_raw.replace("\u2019s", "").replace("'s", "").strip()

        predicted_terms = {"famous painting", "this scene", "the painting"}

        if subj_clean.lower() in predicted_terms and detected_artworks:
            subj_clean = detected_artworks[0]

        if obj_clean.lower() in predicted_terms and detected_artworks:
            obj_clean = detected_artworks[0]

        results.append({
            "subject": subj_clean,
            "predicate": mapped,
            "object": obj_clean,
        })

    return results


def extract_from_text(g):
    """
    Scrape a webpage, extract triples with REBEL, and add them to the graph.
    """
    nlp_model = spacy.load("en_core_web_sm")
    tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
    model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

    url = "https://www.thecollector.com/25-famous-paintings-curated-masterpieces-in-museums/"
    http_response = requests.get(url)
    http_response.raise_for_status()

    html_parser = BeautifulSoup(http_response.text, "html.parser")
    text_from_page = " ".join(html_tag.get_text().strip() for html_tag in html_parser.find_all(["p", "figcaption"]))
    processed_text = re.sub(r"\s+", " ", text_from_page)

    # SpaCy is used for sentence splitting and entity recognition
    spacy_document = nlp_model(processed_text)

    for sentence in spacy_document.sents:
        if not any(ent.label_ in {"PERSON", "WORK_OF_ART", "ORG", "DATE", "LOC", "GPE"} for ent in sentence.ents):
            continue

        triples = extract_sentence_triples(sentence.text, sentence.ents, tokenizer, model)

        for t in triples:
            subj_uri = resolve_uri(t["subject"], g)
            pred_uri = t["predicate"]

            if not subj_uri:
                continue

            if pred_uri in LITERAL_PROPERTIES:
                g.add((subj_uri, pred_uri, Literal(t["object"])))
            else:
                obj_uri = resolve_uri(t["object"], g)

                if obj_uri:
                    g.add((subj_uri, pred_uri, obj_uri))