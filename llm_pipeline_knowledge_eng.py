"""
Requirements: python -m spacy download en_core_web_sm
"""

import requests
from bs4 import BeautifulSoup
import spacy
import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from rdflib import Literal, Namespace
from rdflib.namespace import RDF

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

# Maps each predicate to (subject rdf:type, object rdf:type).
# Subject types are always trusted (all predicates have a well-defined domain).
# Object types are used as fallback when NER does not apply.
TYPE_MAP = {
    MYONT.createdBy:    (MYONT.Painting, MYONT.Artist),
    MYONT.hasTheme:     (MYONT.Painting, MYONT.Theme),
    MYONT.displayedBy:  (MYONT.Painting, MYONT.Museum),
    MYONT.hasPeriod:    (MYONT.Painting, None),
    SCHEMA.dateCreated: (MYONT.Painting, None),
}

# Predicates where the OBJECT type should also be strictly taken from TYPE_MAP, ignoring NER
# types are fully determined by the ontology domain/range.
STRICT_OBJECT_PREDICATES = {MYONT.createdBy, MYONT.displayedBy}

# Maps spaCy NER labels to ontology classes.
NER_CLASS_MAP = {
    "PERSON":      MYONT.Artist,
    "WORK_OF_ART": MYONT.Painting,
    "ORG":         MYONT.Museum,
    "GPE":         MYONT.City,
    "LOC":         MYONT.City,
}

# All instance classes in the ontology, used to check for conflicts
ALL_INSTANCE_CLASSES = {
    MYONT.Painting, MYONT.Artist, MYONT.Museum, MYONT.Theme,
    MYONT.City, MYONT.Sculpture, MYONT.Artifact, MYONT.Vase,
    MYONT.Ceramic, MYONT.Jewellery, MYONT.Scroll, MYONT.Statue,
    MYONT.Figurine,
}


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


def get_existing_type(uri, g):
    """
    Check if a URI already has an rdf:type that is one of our
    instance classes. Returns the first match, or None.
    """
    for _, _, o in g.triples((uri, RDF.type, None)):
        if o in ALL_INSTANCE_CLASSES:
            return o
    return None


def infer_object_type(label, fallback_type, ner_labels, pred_uri):
    """
    Determine the ontology class for a triple's object.

    For strict-object predicates (createdBy, displayedBy), always
    trust TYPE_MAP because the ontology range is definitive.

    For other predicates (hasTheme), allow NER to override.
    """
    if pred_uri in STRICT_OBJECT_PREDICATES:
        return fallback_type

    ner_label = ner_labels.get(label.lower().strip())
    if ner_label and ner_label in NER_CLASS_MAP:
        return NER_CLASS_MAP[ner_label]
    
    return fallback_type


def safe_add_type(uri, new_type, g):
    """
    Add rdf:type to a URI only if it does not conflict with an
    existing type. If the entity already has a different instance
    class, keep the existing one (first-assigned wins).
    """
    if not new_type:
        return

    existing = get_existing_type(uri, g)

    if existing is None:
        g.add((uri, RDF.type, new_type))
    elif existing == new_type:
        pass
    else:
        pass


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

    Type assignment strategy:
    - Subject type: always from TYPE_MAP (all predicates have a well-defined domain of E22_Human_Made_Object / Painting).
    - Object type: from TYPE_MAP for strict-object predicates (createdBy, displayedBy), from NER with TYPE_MAP fallback for others (hasTheme).
    - Conflict prevention: safe_add_type ensures first-assigned type wins.
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

        ner_labels = {}
        for ent in sentence.ents:
            ner_labels[ent.text.lower().strip()] = ent.label_

        triples = extract_sentence_triples(sentence.text, sentence.ents, tokenizer, model)

        for t in triples:
            subj_uri = resolve_uri(t["subject"], g)
            pred_uri = t["predicate"]

            if not subj_uri:
                continue

            # Look up fallback types from TYPE_MAP
            subj_type, obj_fallback = TYPE_MAP.get(pred_uri, (None, None))

            # Subject type always comes from TYPE_MAP (domain is definitive)
            safe_add_type(subj_uri, subj_type, g)
            g.add((subj_uri, SCHEMA.name, Literal(t["subject"])))

            if pred_uri in LITERAL_PROPERTIES:
                g.add((subj_uri, pred_uri, Literal(t["object"])))
            else:
                obj_uri = resolve_uri(t["object"], g)

                if obj_uri:
                    # Object type: strict from TYPE_MAP or NER-assisted
                    obj_type = infer_object_type(
                        t["object"], obj_fallback, ner_labels, pred_uri
                    )
                    safe_add_type(obj_uri, obj_type, g)
                    g.add((obj_uri, SCHEMA.name, Literal(t["object"])))

                    g.add((subj_uri, pred_uri, obj_uri))