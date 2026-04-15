import requests                          # For downloading webpage HTML
from bs4 import BeautifulSoup            # For parsing HTML content
import spacy                             # For NLP (sentence splitting + entities)
import re                                # For text cleaning
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # REBEL model


nlp_model = spacy.load("en_core_web_sm")

url = "https://www.thecollector.com/25-famous-paintings-curated-masterpieces-in-museums/"

http_response = requests.get(url)

html_parser = BeautifulSoup(http_response.text, "html.parser")
html_scraped = html_parser.find_all(['p', 'figcaption'])


text_from_page = " ".join([
    html_tag.get_text().strip() for html_tag in html_scraped
])


processed_text = re.sub(r'\s+', ' ', text_from_page)

# SpaCy is used for sentence splitting and entity recognition
spacy_document = nlp_model(processed_text)


# Model is used for relation/triple extraction
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

model.config.max_length = None


# Maps predicted relations from the model to our ontology predicates
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
    "PERSON": "foaf:Person",
    "WORK_OF_ART": "myont:Artwork",
    "ORG": "schema:Organization",
    "GPE": "schema:Place",
    "LOC": "schema:Place",
    "DATE": "schema:Date"
}


def output_length(input_sentence):
    """
    Determines how long the generated output can be.
    """
    return len(input_sentence.split()) + 128


def parse_generated_text(rebel_output_text):
    """
    REBEL outputs special tokens like:
    <triplet> <subj> ... <obj> ... <relation>

    This function converts that into:
    (subject, relation, object)
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
            # Append token based on current parsing state
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

def create_entity_triples(spacy_entities):

    type_triples = []

    for entity in spacy_entities:
        entity_name = entity.text.strip()
        entity_label = entity.label_

        mapped_type = ENTITY_MAP.get(entity_label)

        if mapped_type:
            triple = f"({entity_name}, rdf:type, {mapped_type})"
            type_triples.append(triple)

    return list(set(type_triples))


def extract_rdf_triples(sentence_text, spacy_entities):

    tokenized_input = tokenizer(sentence_text, return_tensors="pt")

    generated_output_tokens = model.generate(
        **tokenized_input,
        max_new_tokens=128,
        num_beams=3,
        early_stopping=True,
        max_length=output_length(sentence_text)
    )

    decoded_output_text = tokenizer.batch_decode(
        generated_output_tokens,
        skip_special_tokens=False
    )[0]


    output_triples = parse_generated_text(decoded_output_text)

    processed_triples = []

    # Extract detected artwork names for subject identification
    detected_artworks = [
        entity.text for entity in spacy_entities if entity.label_ == "WORK_OF_ART"
    ]

    # Lowercase entity list for fuzzy matching
    list_of_entities = [
        entity.text.lower().strip() for entity in spacy_entities
    ]

    for triple in output_triples:

        raw_relation = triple['type'].lower()

        mapped_relation = RELATION_MAP.get(raw_relation)
        if mapped_relation:

            subject_raw = triple['head']
            object_raw = triple['tail']

            subject_lower = subject_raw.lower()
            object_lower = object_raw.lower()

            match_found = any(
                ent in subject_lower or subject_lower in ent or
                ent in object_lower or object_lower in ent
                for ent in list_of_entities
            )

            if match_found:

                subject_clean = subject_raw.replace("'s", "").replace("’s", "").strip()
                object_clean = object_raw.replace("'s", "").replace("’s", "").strip()

                predicted_terms = ["famous painting", "this scene", "the painting"]

                if subject_clean.lower() in predicted_terms and detected_artworks:
                    subject_clean = detected_artworks[0]

                if object_clean.lower() in predicted_terms and detected_artworks:
                    object_clean = detected_artworks[0]

                processed_triples.append(
                    f"({subject_clean}, {mapped_relation}, {object_clean})"
                )

    # Remove duplicates
    return "\n".join(set(processed_triples))



# Loop through each sentence detected by spaCy
for sentence in spacy_document.sents:

    if any(entity.label_ in ["PERSON", "WORK_OF_ART", "ORG", "DATE", "LOC", "GPE"]
           for entity in sentence.ents):

        relation_triples = extract_rdf_triples(
            sentence.text,
            sentence.ents
        )

        type_triples = create_entity_triples(sentence.ents)

        if relation_triples:

            print(f"Sentence: {sentence.text[:100]}...")

            print("Relation Triples:")
            print(relation_triples)

            print("Type Triples:")
            for triple in type_triples:
                print(triple)

            print("-" * 50)
