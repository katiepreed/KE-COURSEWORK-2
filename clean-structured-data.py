
RELATION_MAP = {
    "artist": "myont:createdBy",
    "creator": "myont:createdBy",
    "year": "schema:dateCreated",
    "date": "schema:dateCreated",
    "museum": "myont:displayedBy",
    "location": "myont:displayedBy"
}

def clean_structured_record(raw_record):
   
    triples = []
   
    subject = raw_record.get("title", "").lower().strip()
    for key, value in raw_record.items():

        field_name = key.lower()
        field_value = str(value).lower().strip()

        # Skip title (already used as subject)
        if field_name == "title":
            continue

        # Map relation to ontology
        predicate = RELATION_MAP.get(field_name)

        if not predicate:
            continue  # skip unknown fields


        triple = f"({subject}, {predicate}, {field_value})"
        triples.append(triple)

    return triples