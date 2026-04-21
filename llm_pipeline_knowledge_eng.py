import re
import requests
from bs4 import BeautifulSoup
import spacy
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from rdflib import Literal
from rdflib.namespace import RDF, XSD
from uri_utils import make_uri, MYONT, PREFIX_MAP, bind_namespaces

RELATION_MAP = {
    "creator": "myont:createdBy",
    "author": "myont:createdBy",
    "painter": "myont:createdBy",

    "movement": "myont:hasPeriod",
    "style": "myont:hasPeriod",

    "genre": "myont:hasTheme",
    "main subject": "myont:hasTheme",
    "depicts": "myont:hasTheme",

    "inception": "schema:dateCreated",
    "point in time": "schema:dateCreated",
    "date of production": "schema:dateCreated",

    "location": "myont:displayedBy",
    "exhibited at": "myont:displayedBy",
    "subsidiary": "myont:displayedBy",
    "collection": "myont:displayedBy"
}

ENTITY_MAP = {
    "PERSON": "crm:E21_Person",
    "WORK_OF_ART": "myont:Painting",
    "ORG": "myont:Museum",
    "GPE": "myont:Country",
    "LOC": "crm:E53_Place",
}

LITERAL_PREDICATES = {"schema:dateCreated", "myont:hasPeriod"}

THEME_SUBCLASS_MAP = {
    "nature": MYONT.NatureTheme,
    "landscape": MYONT.NatureTheme,
    "animal": MYONT.AnimalTheme,
    "animals": MYONT.AnimalTheme,
    "religious": MYONT.ReligiousTheme,
    "religion": MYONT.ReligiousTheme,
    "biblical": MYONT.ReligiousTheme,
    "mythological": MYONT.MythologicalTheme,
    "mythology": MYONT.MythologicalTheme,
    "myth": MYONT.MythologicalTheme,
}

def resolve_prefixed(prefixed):
    prefix, local = prefixed.split(":", 1)
    return PREFIX_MAP[prefix][local]

def output_length(input_sentence):
    return len(input_sentence.split()) + 128

def parse_generated_text(rebel_output_text):
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
                    "tail": current_object.strip(),
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
            "tail": current_object.strip(),
        })

    return extracted_triples

def create_entity_triples(spacy_entities, g, known_uris):
    for entity in spacy_entities:
        entity_name = entity.text.strip()
        mapped_type = ENTITY_MAP.get(entity.label_)

        if not mapped_type:
            continue

        # to reduce duplication
        if any(word in entity_name.lower() for word in ["met", "gogh", "monet", "paris", "toledo", "york"]):
            continue

        subject_uri = make_uri(entity_name)
        type_uri = resolve_prefixed(mapped_type)
        g.add((subject_uri, RDF.type, type_uri))
        known_uris.add(subject_uri)  # track typed entities


def add_theme_triple(subject_node, predicate_node, object_text, g, known_uris):
    """
    Special handling for hasTheme: create a Theme instance, type it to the
    most specific Theme subclass we can detect, and link it to the subject.
    """
    theme_instance = make_uri(object_text)
    g.add((subject_node, predicate_node, theme_instance))

    # Default to the generic Theme class, then try to upgrade.
    theme_class = MYONT.Theme
    object_lower = object_text.lower()
    for keyword, subclass in THEME_SUBCLASS_MAP.items():
        if keyword in object_lower:
            theme_class = subclass
            break

    g.add((theme_instance, RDF.type, theme_class))
    known_uris.add(theme_instance)  # theme instances are explicitly typed so track them


def extract_rdf_triples(sentence_text, spacy_entities, tokenizer, model, g, known_uris):
    tokenized_input = tokenizer(sentence_text, return_tensors="pt")
    generated_output_tokens = model.generate(
        **tokenized_input,
        max_new_tokens=128,
        num_beams=3,
        early_stopping=True
    )

    decoded_output_text = tokenizer.batch_decode(
        generated_output_tokens, skip_special_tokens=False
    )[0]

    output_triples = parse_generated_text(decoded_output_text)

    detected_artworks = [
        entity.text for entity in spacy_entities if entity.label_ == "WORK_OF_ART"
    ]
    list_of_entities = [e.text.lower().strip() for e in spacy_entities]
    predicted_terms = {"famous painting", "this scene", "the painting"}

    for triple in output_triples:
        raw_relation = triple["type"].lower()
        mapped_relation = RELATION_MAP.get(raw_relation)
        if not mapped_relation:
            continue

        subject_raw = triple["head"]
        object_raw = triple["tail"]
        subject_lower = subject_raw.lower()
        object_lower = object_raw.lower()

        match_found = any(
            ent in subject_lower or subject_lower in ent or
            ent in object_lower or object_lower in ent
            for ent in list_of_entities
        )

        if not match_found:
            continue

        subject_clean = subject_raw.replace("'s", "").replace("\u2019s", "").strip()
        object_clean = object_raw.replace("'s", "").replace("\u2019s", "").strip()

        if subject_clean.lower() in predicted_terms and detected_artworks:
            subject_clean = detected_artworks[0]
        if object_clean.lower() in predicted_terms and detected_artworks:
            object_clean = detected_artworks[0]

        subject_node = make_uri(subject_clean)
        predicate_node = resolve_prefixed(mapped_relation)

        # only add triples where the subject is a known typed entity
        if subject_node not in known_uris:
            continue

        if mapped_relation == "myont:hasTheme":
            add_theme_triple(subject_node, predicate_node, object_clean, g, known_uris)
        elif mapped_relation in LITERAL_PREDICATES:
            # dates and period strings go in as literals
            object_node = Literal(object_clean, datatype=XSD.string)
            g.add((subject_node, predicate_node, object_node))
        else:
            object_node = make_uri(object_clean)
            if object_node in known_uris:
                g.add((subject_node, predicate_node, object_node))

def extract_from_text(g):
    bind_namespaces(g)

    known_uris = set()  # tracks all explicitly typed entity URIs

    nlp_model = spacy.load("en_core_web_sm")
    tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
    model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
    model.config.max_length = None

    url = "https://www.thecollector.com/25-famous-paintings-curated-masterpieces-in-museums/"
    http_response = requests.get(url)

    html_parser = BeautifulSoup(http_response.text, "html.parser")
    html_scraped = html_parser.find_all(["p", "figcaption"])
    text_from_page = " ".join(
        tag.get_text().strip() for tag in html_scraped
    )
    processed_text = re.sub(r"\s+", " ", text_from_page)

    spacy_document = nlp_model(processed_text)

    for sentence in spacy_document.sents:
        if not any(
            ent.label_ in {"PERSON", "WORK_OF_ART", "ORG", "DATE", "LOC", "GPE"}
            for ent in sentence.ents
        ):
            continue

        create_entity_triples(sentence.ents, g, known_uris)
        extract_rdf_triples(sentence.text, sentence.ents, tokenizer, model, g, known_uris)