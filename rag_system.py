"""
Ontology gaps:
O1. Missing gender property on artists
O2. No Artistic Movement class / object property
O3. No LocatedIn object property for museums / places
O4. Cities / countries / regions are not connected via transitive property
O5. No Medium class / object property for artworks

Instance gaps:
I1. Populate nationality values for artists that are missing one
I2. Create artistic movements and assign as values to property field
I3. Populate the location of museums in the ontology, create new locations if they do not exist
I4. Create theme instances and assign to instances that are missing a value for the property field
I5. Create medium instances and assign as values to fields

Instructions: 

1. Download Ollama: https://ollama.com/download
2. Open Ollama or make sure ollama is running with "ollama serve"
3. Pull llama model in the terminal: ollama pull llama3
4. Set environment variable: 
- macOS: 
    - export OLLAMA_MODEL=llama3
- windows: 
    - set OLLAMA_MODEL=llama3
4. Run file: python rag_system.py
"""
import os
import re
import time
import requests

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD
from uri_utils import make_uri, MYONT, SCHEMA, CRM, resolve_alias

SYSTEM_PROMPT = (
    "You are a concise art history assistant. "
    "Answer with a single short phrase or exact format requested. "
    "No extra explanation, no full sentences."
)

BUILTIN_LABELS = ["Nature", "Animal", "Religious", "Mythological"]

UNCERTAINTY_WORDS = ["probably", "possibly", "likely", "perhaps", "maybe"]

DEFAULT_NEGATIVE_PHRASES = [
    "no such", "not found", "unknown", "i don't", "i do not",
    "no information", "none", "n/a",
    "uncertain", "unclear", "not sure", "i think", "i believe"
]

def ask_llm(prompt: str, system: str = "") -> str:
    """
    Query the local Ollama llama model and return the response text.
    """
    model = os.environ.get("OLLAMA_MODEL")

    if not model:
        raise RuntimeError(
            "No llama backend configured. Set OLLAMA_MODEL and ensure Ollama is running."
        )

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    try:
        resp = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 256,
                    "seed": 42,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        response_text = resp.json().get("response", "").strip()
        if not response_text:
            raise RuntimeError("Ollama returned an empty response.")
        return response_text
    except Exception as exc:
        raise RuntimeError(f"LLM query failed: {exc}") from exc

def clean_llm_label(raw: str, start_phrase: list[str] | None = None, phrase_mode: str = "startswith") -> str:
    start_phrase = start_phrase or []

    raw = raw.strip().strip("\"'.,;")
    raw = raw.split("\n")[0].split(".")[0].strip()

    if any(phrase in raw.lower() for phrase in DEFAULT_NEGATIVE_PHRASES):
        return ""
      
    if re.search(r"\bor\b", raw.lower()):
        return ""
  
    for phrase in start_phrase:
        if phrase_mode == "startswith":
            if raw.lower().startswith(phrase):
                raw = raw[len(phrase):].strip()
        else:  # "contains"
            if phrase in raw.lower():
                raw = raw.lower().split(phrase)[-1].strip()

    for wrd in UNCERTAINTY_WORDS:
        if raw.lower().startswith(wrd + " "):
            raw = raw[len(wrd):].strip()
            break 

    return raw.title()

def clean_location(raw: str) -> tuple[str, str]:
    raw = raw.strip().split("\n")[0]

    raw = re.sub(r"^probably[_\s]+", "", raw, flags=re.IGNORECASE)

    if " or " in raw.lower():
        return "", ""

    if any(phrase in raw.lower() for phrase in DEFAULT_NEGATIVE_PHRASES):
        return "", ""

    parts = [p.strip() for p in raw.split(",")]
    city    = resolve_alias(parts[0]) if parts else ""
    country = resolve_alias(parts[1]) if len(parts) > 1 else ""

    return city, country

def clean_gender(raw: str) -> str:
    if re.search(r"\bor\b", raw.lower()):
        return ""
    
    raw = raw.strip().strip("\"'.,;")
    raw = raw.split("\n")[0].split(".")[0].strip().lower()

    if "female" in raw or raw in {"f", "woman", "women"}:
        return "female"
    if "non-binary" in raw or "nonbinary" in raw:
        return "non-binary"
    if "male" in raw or raw in {"m", "man", "men"}:
        return "male"
    if "unknown" in raw:
        return "unknown"

    return ""

def rag_I1(g: Graph) -> tuple[int, int]:
    """
    Fill missing artist nationality via RAG.
    """
    count = 0

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist ?name WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        FILTER NOT EXISTS { ?artist myont:hasNationality ?n }
    }
    """

    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        artist_uri = row.artist
        name = str(row.name)

        prompt = (
            f"What is the nationality of the artist named '{name}'? "
            "Reply with a single nationality word or short phrase only."
        )

        raw = ask_llm(prompt, system=SYSTEM_PROMPT)
        nat = clean_llm_label(raw, start_phrase=["nationality:", "their nationality is", "was", "is"])
        time.sleep(0.1)

        if not nat:
            continue

        g.add((artist_uri, MYONT.hasNationality, Literal(nat, datatype=XSD.string)))
        g.add((artist_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a nationality triple!")

    return count, candidates

def rag_O5_I5(g: Graph) -> tuple[int, int]:
    """
    Create primaryMedium property and Medium class that is extracted from the medium description. 
    """
    count = 0

    if (MYONT.Medium, RDF.type, OWL.Class) not in g:
        g.add((MYONT.Medium, RDF.type, OWL.Class))
        g.add((MYONT.Medium, RDFS.label, Literal("Medium")))
        g.add((MYONT.Medium, RDFS.comment, Literal("The primary material or technique used to create an artwork.")))

    if (MYONT.hasPrimaryMedium, RDF.type, OWL.ObjectProperty) not in g:
        g.add((MYONT.hasPrimaryMedium, RDF.type, OWL.ObjectProperty))
        g.add((MYONT.hasPrimaryMedium, RDFS.label, Literal("has medium")))
        g.add((MYONT.hasPrimaryMedium, RDFS.domain, CRM.E22_Human_Made_Object))
        g.add((MYONT.hasPrimaryMedium, RDFS.range, MYONT.Medium))

    sparql = """
    PREFIX myont: <https://ontologeez/>
    SELECT DISTINCT ?artwork ?desc WHERE {
        ?artwork myont:mediumDescription ?desc .
    }
    """

    desc_cache = {}

    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        artwork_uri = row.artwork
        desc = str(row.desc).strip().lower()

        if (artwork_uri, MYONT.hasPrimaryMedium, None) in g:
            continue

        if desc not in desc_cache:
            prompt = (
                f"Medium description: '{desc}'. "
                "What is the single primary medium or material? "
                "Reply with a short label only, e.g. 'Oil Paint', 'Bronze', 'Watercolour'."
            )
            medium_label = clean_llm_label(ask_llm(prompt, system=SYSTEM_PROMPT), start_phrase=["primary medium:", "the primary medium is", "medium:"])
            time.sleep(0.05)
            desc_cache[desc] = medium_label

        medium_label = desc_cache[desc]

        if not medium_label:
            continue

        medium_uri = make_uri(medium_label)

        if (medium_uri, RDF.type, MYONT.Medium) not in g:
            g.add((medium_uri, RDF.type, MYONT.Medium))
            g.add((medium_uri, RDFS.label, Literal(medium_label)))

        g.add((artwork_uri, MYONT.hasPrimaryMedium, medium_uri))
        g.add((artwork_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a medium triple!")

    return count, candidates

def rag_O3_I3(g: Graph) -> tuple[int, int]:
    """
    Populate locatedIn field for museums.
    """
    count = 0

    if (MYONT.locatedIn, RDF.type, OWL.TransitiveProperty) not in g:
        g.add((MYONT.locatedIn, RDF.type, OWL.ObjectProperty))
        g.add((MYONT.locatedIn, RDF.type, OWL.TransitiveProperty))
        g.add((MYONT.locatedIn, RDFS.label, Literal("located in")))
        g.add((MYONT.locatedIn, RDFS.comment, Literal("A place located inside a larger place. Used for museum -> city, city -> country, and country ->region.")))
        g.add((MYONT.locatedIn, RDFS.range, CRM.E53_Place))

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?museum ?name WHERE {
        ?museum rdf:type myont:Museum .
        OPTIONAL { ?museum schema:name ?name }
        FILTER NOT EXISTS { ?museum myont:locatedIn ?loc }
    }
    """
    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        museum_uri = row.museum

        if row.name:
            museum_label = str(row.name)
        else:
            museum_label = str(museum_uri).split("/")[-1].replace("_", " ")

        prompt = (
            f"In which city is the museum '{museum_label}' located? "
            "Reply in the format 'City, Country' only e.g. 'Paris, France'."
        )

        raw = ask_llm(prompt, system=SYSTEM_PROMPT)
        city, country = clean_location(raw)
        time.sleep(0.1)

        if not city or len(city) < 2:
            continue

        city_uri = make_uri(city)

        if (city_uri, RDF.type, MYONT.Country) in g or (city_uri, RDF.type, MYONT.Region) in g:
            continue

        if (city_uri, RDF.type, MYONT.City) not in g:
            g.add((city_uri, RDF.type, MYONT.City))
            g.add((city_uri, RDFS.label, Literal(city)))
            g.add((city_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))

        g.add((museum_uri, MYONT.locatedIn, city_uri))
        g.add((museum_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a museum location triple!")

    return count, candidates

def rag_O2_I2(g: Graph) -> tuple[int, int]:
    """
    Create class and field for artistic movement and populate instances / values for fields. 
    """
    count = 0

    if (MYONT.ArtisticMovement, RDF.type, OWL.Class) not in g:
        g.add((MYONT.ArtisticMovement, RDF.type, OWL.Class))
        g.add((MYONT.ArtisticMovement, RDFS.label, Literal("Artistic Movement")))
        g.add((MYONT.ArtisticMovement, RDFS.comment, Literal("A named artistic movement, school, or style (e.g. Impressionism).")))

    if (MYONT.associatedWithMovement, RDF.type, OWL.ObjectProperty) not in g:
        g.add((MYONT.associatedWithMovement, RDF.type, OWL.ObjectProperty))
        g.add((MYONT.associatedWithMovement, RDFS.label, Literal("associated with movement")))
        g.add((MYONT.associatedWithMovement, RDFS.domain, MYONT.Artist))
        g.add((MYONT.associatedWithMovement, RDFS.range, MYONT.ArtisticMovement))

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist ?name ?nationality WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        OPTIONAL { ?artist myont:hasNationality ?nationality }
    }
    """

    title_sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?name ?title WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        ?artwork myont:createdBy ?artist .
        ?artwork schema:name ?title .
    } LIMIT 200
    """

    artist_titles = {}
    for row in g.query(title_sparql):
        artist_titles.setdefault(str(row.name), []).append(str(row.title))

    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        artist_uri = row.artist
        name = str(row.name)
        nationality = str(row.nationality) if row.nationality else ""

        if (artist_uri, MYONT.associatedWithMovement, None) in g:
            continue

        titles = artist_titles.get(name, [])[:5]
        titles_text = ", ".join(f'"{t}"' for t in titles) if titles else "unknown"
        nat_text = f"nationality {nationality}" if nationality else ""
        context = f" ({nat_text})" if nat_text else ""

        prompt = (
            f"Artist: {name}{context}. "
            f"Representative works: {titles_text}. "
            f"What single artistic movement or style is this artist most associated with?"
        )

        movement = clean_llm_label(ask_llm(prompt, system=SYSTEM_PROMPT), start_phrase=["is associated with", "was associated with", "belongs to", "is best known as part of", "is a member of", "the movement is", "movement:"], phrase_mode="contains")
        time.sleep(0.1)

        if not movement:
            continue

        movement_uri = make_uri(movement)
        if (movement_uri, RDF.type, MYONT.ArtisticMovement) not in g:
            g.add((movement_uri, RDF.type, MYONT.ArtisticMovement))
            g.add((movement_uri, RDFS.label, Literal(movement)))

        g.add((artist_uri, MYONT.associatedWithMovement, movement_uri))
        g.add((artist_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added an artistic movement triple!")

    return count, candidates

def classify_theme(label: str) -> str:
    prompt = (
        f"Does the theme '{label}' fit into one of these categories: "
        "Nature, Animal, Religious, Mythological? "
        "If yes, reply with only the matching category name. "
        "If no, reply with 'None'."
    )
    raw = ask_llm(prompt, system=SYSTEM_PROMPT).strip().strip("\"'.,;")
    result = raw.split("\n")[0].strip().title()
    return result if result in BUILTIN_LABELS else ""

def resolve_theme(g: Graph, label: str) -> URIRef:
    """
    Create new theme instances if they do not exist.
    """
    builtin_label = classify_theme(label)

    if builtin_label:
        # map the label to the corresponding ontology class
        theme_class = MYONT[f"{builtin_label}Theme"]
        class_local = f"{builtin_label}Theme"
        instance_uri = MYONT[f"{class_local}_instance"]

        if (instance_uri, RDF.type, theme_class) not in g:
            g.add((instance_uri, RDF.type, theme_class))
            g.add((instance_uri, RDFS.label, Literal(builtin_label)))

        return instance_uri

    # create a new theme
    instance_uri = make_uri(label)
    if (instance_uri, RDF.type, MYONT.Theme) not in g:
        g.add((instance_uri, RDF.type, MYONT.Theme))
        g.add((instance_uri, RDFS.label, Literal(label.title())))
        g.add((instance_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))

    return instance_uri

def rag_I4(g: Graph) -> tuple[int, int]:
    """
    Populate hasTheme on artworks that lack one.
    """
    count = 0

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artwork ?title ?artistName ?medium WHERE {
        ?artwork rdf:type ?t .
        FILTER(?t IN (<https://ontologeez/Painting>,
                      <https://ontologeez/Sculpture>,
                      <https://ontologeez/Statue>,
                      <https://ontologeez/Figurine>,
                      <https://ontologeez/Vase>,
                      <https://ontologeez/Ceramic>,
                      <https://ontologeez/Scroll>,
                      <https://ontologeez/Jewellery>))
        OPTIONAL { ?artwork schema:name ?title }
        OPTIONAL { ?artwork myont:createdBy ?artist .
                   ?artist  schema:name ?artistName }
        OPTIONAL { ?artwork myont:mediumDescription ?medium }
        FILTER NOT EXISTS { ?artwork myont:hasTheme ?th }
    }
    """

    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        artwork_uri = row.artwork
        title = str(row.title) if row.title else ""
        artist_name = str(row.artistName) if row.artistName else ""
        medium = str(row.medium) if row.medium else ""

        if not title and not artist_name:
            continue

        ctx_parts = []

        if artist_name:
            ctx_parts.append(f"by {artist_name}")
        if medium:
            ctx_parts.append(f"medium: {medium}")

        ctx = " (" + ", ".join(ctx_parts) + ")" if ctx_parts else ""

        prompt = (
            f"Artwork: '{title or 'untitled'}'{ctx}. "
            "Classify the subject of this artwork with a single theme label. "
            "Prefer one of 'Nature', 'Animal', 'Religious', 'Mythological' "
            "when applicable. Otherwise give a short new theme label "
            "(e.g. 'Portrait', 'Still Life', 'Battle', 'Daily Life'). "
            "Reply with the theme label only."
        )

        raw = ask_llm(prompt, system=SYSTEM_PROMPT)
        theme_label = clean_llm_label(raw, start_phrase=[])
        time.sleep(0.1)

        if not theme_label:
            continue

        theme_uri = resolve_theme(g, theme_label)
        g.add((artwork_uri, MYONT.hasTheme, theme_uri))
        g.add((artwork_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a theme triple!")

    return count, candidates

def rag_O1(g: Graph) -> tuple[int, int]:
    """
    Define gender property and assign via RAG.
    """
    count = 0

    if (MYONT.hasGender, RDF.type, OWL.DatatypeProperty) not in g:
        g.add((MYONT.hasGender, RDF.type, OWL.DatatypeProperty))
        g.add((MYONT.hasGender, RDFS.domain, MYONT.Artist))
        g.add((MYONT.hasGender, RDFS.range, XSD.string))
        g.add((MYONT.hasGender, RDFS.label, Literal("has gender")))
        g.add((MYONT.hasGender, RDFS.comment, Literal("The gender of an artist.")))

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist ?name ?nationality  WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        OPTIONAL { ?artist myont:hasNationality ?nationality }
        FILTER NOT EXISTS { ?artist myont:hasGender ?g }
    }
    """

    rows = list(g.query(sparql))
    candidates = len(rows)
    for row in rows:
        artist_uri  = row.artist
        name = str(row.name)
        nationality = str(row.nationality) if row.nationality else ""

        ctx_parts = []

        if nationality:
            ctx_parts.append(f"nationality {nationality}")

        ctx = f" ({', '.join(ctx_parts)})" if ctx_parts else ""

        prompt = (
            f"Artist: {name}{ctx}. "
            "What is the gender of this identified artist? "
            "Reply with exactly one word: 'male', 'female', 'non-binary', or "
            "'unknown'."
        )

        raw = ask_llm(prompt, system=SYSTEM_PROMPT)
        gender = clean_gender(raw)

        time.sleep(0.1)

        if not gender:
            continue

        g.add((artist_uri, MYONT.hasGender, Literal(gender, datatype=XSD.string)))
        g.add((artist_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a gender triple!")

    return count, candidates

def rag_O4(g: Graph) -> tuple[int, int]:
    """
    Connect cities -> countries -> regions using the locatedIn property. 
    """
    count = 0

    city_sparql = """
    PREFIX myont: <https://ontologeez/>
    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?city ?label WHERE {
        ?city rdf:type myont:City .
        OPTIONAL { ?city rdfs:label ?label }
        FILTER NOT EXISTS {
            ?city myont:locatedIn ?c .
            ?c rdf:type myont:Country .
        }
    }
    """

    city_rows = list(g.query(city_sparql))
    candidates = len(city_rows)
    for row in city_rows:
        city_uri = row.city
        city_label = str(row.label) if row.label else str(city_uri).split("/")[-1].replace("_", " ")

        prompt = (
            f"In which country is the city '{city_label}' located? "
            "Reply with only the country name, e.g. 'France'."
        )

        country = clean_llm_label(ask_llm(prompt, system=SYSTEM_PROMPT), start_phrase=["country:", "the country is", "it is in", "located in"])
        time.sleep(0.1)

        if not country:
            continue

        country_uri = make_uri(country)

        if (country_uri, RDF.type, MYONT.City) in g or (country_uri, RDF.type, MYONT.Region) in g:
            continue

        if (country_uri, RDF.type, MYONT.Country) not in g:
            g.add((country_uri, RDF.type, MYONT.Country))
            g.add((country_uri, RDFS.label, Literal(country)))
            g.add((country_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))

        g.add((city_uri, MYONT.locatedIn, country_uri))
        g.add((city_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a triple!")

    country_sparql = """
    PREFIX myont: <https://ontologeez/>
    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?country ?label WHERE {
        ?country rdf:type myont:Country .
        OPTIONAL { ?country rdfs:label ?label }
        FILTER NOT EXISTS {
            ?country myont:locatedIn ?r .
            ?r rdf:type myont:Region .
        }
    }
    """

    country_rows = list(g.query(country_sparql))
    candidates += len(country_rows)
    for row in country_rows:
        country_uri = row.country
        country_label = str(row.label) if row.label else str(country_uri).split("/")[-1].replace("_", " ")

        prompt = (
            f"Which geographic region is the country '{country_label}' part of? "
            "Use a standard region such as 'Western Europe', 'Eastern Europe', "
            "'Northern Europe', 'Southern Europe', 'North America', 'South America', "
            "'Central America', 'East Asia', 'South Asia', 'Southeast Asia', "
            "'Central Asia', 'Western Asia', 'North Africa', 'Sub-Saharan Africa', "
            "'Oceania', or 'Caribbean'. Reply with only the region name."
        )

        region = clean_llm_label(ask_llm(prompt, system=SYSTEM_PROMPT), start_phrase=["region:", "the region is", "it is in", "part of"])
        time.sleep(0.1)

        if not region:
            continue

        region_uri = make_uri(region)

        if (region_uri, RDF.type, MYONT.City) in g or (region_uri, RDF.type, MYONT.Country) in g:
            continue

        if (region_uri, RDF.type, MYONT.Region) not in g:
            g.add((region_uri, RDF.type, MYONT.Region))
            g.add((region_uri, RDFS.label, Literal(region)))
            g.add((region_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))

        g.add((country_uri, MYONT.locatedIn, region_uri))
        g.add((country_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        count += 1

        print("Added a triple!")

    return count, candidates

def run_rag_pipeline(input_ttl: str, output_ttl: str) -> None:
    g = Graph()
    g.parse(input_ttl, format="turtle")
    g.bind("myont", MYONT)
    g.bind("schema", SCHEMA)
    g.bind("crm", CRM)

    if (MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty) not in g:
        g.add((MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty))
        g.add((MYONT.ragGenerated, RDFS.label, Literal("RAG generated")))
        g.add((MYONT.ragGenerated, RDFS.comment, Literal("True if this triple was generated by the RAG system rather than from the structured data pipeline.")))

    counts = {
        "I1 (nationality)":         rag_I1(g),
        "O2/I2 (movement)":         rag_O2_I2(g),
        "O3/I3 (museum location)":  rag_O3_I3(g),
        "I4 (theme)":               rag_I4(g),
        "O1 (gender)":              rag_O1(g),
        "O4 (city/country/region)": rag_O4(g),
        "O5/I5 (medium)":           rag_O5_I5(g),
    }

    g.serialize(destination=output_ttl, format="turtle")

    total_filled = total_candidates = 0

    for gap, (filled, candidates) in counts.items():
        coverage = (filled / candidates * 100) if candidates else 0.0
        print(f"{gap:<26} {filled:>6}  {candidates:>10}  {coverage:>7.1f}%")
        total_filled += filled
        total_candidates += candidates

    total_coverage = (total_filled / total_candidates * 100) if total_candidates else 0.0

    print(f"{'TOTAL':<26} {total_filled:>6}  {total_candidates:>10}  {total_coverage:>7.1f}%")

if __name__ == "__main__":
    run_rag_pipeline("art_and_museum_ontology.ttl", "rag_output.ttl")