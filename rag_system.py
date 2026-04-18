"""
RAG System for Knowledge Graph Completion
==========================================
Phase 6 of the Knowledge Engineering pipeline.

This script implements Retrieval Augmented Generation (RAG) to resolve
identified gaps in the art and museum knowledge graph.

Gaps addressed:
  O1 - Missing myont:hasGender property             (code fix — populated from data.json)
  O2 - No ArtisticMovement class or associations    (RAG — LLM suggests movement per artist)
  O3 - Museum has no location triple                (code fix — direct triple insertion)
  O4 - Medium is unstructured text only             (RAG — LLM normalises mediumDescription)
  O5 - Painter/Sculptor not explicitly typed        (code fix — post-processing step)
  I1 - Many artists missing nationality             (RAG — LLM suggests nationality)
  I2 - Many artists missing birth/death dates       (RAG — LLM suggests dates)

RAG approach (per completion analysis document):
  1. SPARQL queries retrieve existing context from the KG.
  2. Context is verbalised into natural language.
  3. An LLM is prompted with the enriched context to suggest missing triples.
  4. All RAG-generated triples are annotated with myont:ragGenerated true.

LLM backends (auto-detected, in priority order):
  1. Ollama  — free, runs locally. Set OLLAMA_MODEL (e.g. "llama3").
                Requires `ollama serve` running on http://localhost:11434.
  2. Groq    — free tier cloud API. Set GROQ_API_KEY.
  3. Anthropic — paid. Set ANTHROPIC_API_KEY.
  4. Fallback — pre-computed answer tables (no network needed).

Usage:
    pip install rdflib requests
    # Pick ONE of the following:
    #   (a) Free local — install Ollama, then:
    #         ollama pull llama3
    #         export OLLAMA_MODEL=llama3
    #   (b) Free cloud — get a key at https://console.groq.com/ then:
    #         export GROQ_API_KEY=gsk_...
    #   (c) Paid — export ANTHROPIC_API_KEY=sk-ant-...
    #   (d) None  — runs offline using the fallback tables.
    python rag_system.py [--input art_and_museum_ontology.ttl] [--output rag_output.ttl]
"""

import argparse
import json
import os
import re
import sys
import time

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
MYONT  = Namespace("https://ontologeez/")
SCHEMA = Namespace("https://schema.org/")
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")

# ---------------------------------------------------------------------------
# Pre-computed fallback answers (used when ANTHROPIC_API_KEY is not set)
# This allows the pipeline to be demonstrated without network access.
# ---------------------------------------------------------------------------
FALLBACK_MOVEMENTS = {
    "Claude Monet":            "Impressionism",
    "Pierre-Auguste Renoir":   "Impressionism",
    "Edgar Degas":             "Impressionism",
    "Paul Cézanne":            "Post-Impressionism",
    "Vincent van Gogh":        "Post-Impressionism",
    "Georges Seurat":          "Pointillism",
    "Paul Gauguin":            "Post-Impressionism",
    "Henri Matisse":           "Fauvism",
    "Pablo Picasso":           "Cubism",
    "Rembrandt van Rijn":      "Dutch Golden Age",
    "Johannes Vermeer":        "Dutch Golden Age",
    "Frans Hals":              "Dutch Golden Age",
    "Peter Paul Rubens":       "Baroque",
    "Caravaggio":              "Baroque",
    "Michelangelo":            "Renaissance",
    "Leonardo da Vinci":       "Renaissance",
    "Raphael":                 "Renaissance",
    "Sandro Botticelli":       "Early Renaissance",
    "El Greco":                "Mannerism",
    "Francisco Goya":          "Romanticism",
    "Eugène Delacroix":        "Romanticism",
    "Gustave Courbet":         "Realism",
    "Édouard Manet":           "Realism",
    "Winslow Homer":           "American Realism",
    "John Singer Sargent":     "Impressionism",
    "Mary Cassatt":            "Impressionism",
    "Camille Pissarro":        "Impressionism",
    "Alfred Sisley":           "Impressionism",
    "Berthe Morisot":          "Impressionism",
    "Charles Henry Alston":    "Harlem Renaissance",
    "Rosa Bonheur":            "Realism",
    "Leonora Carrington":      "Surrealism",
}

FALLBACK_NATIONALITIES = {
    "Mustafa ibn Vali":        ("Ottoman", None, None),
    "Bi Chang":                ("Chinese", None, None),
    "Fly Furayi":              ("Zimbabwean", None, None),
    "Henry Munyaradzi":        ("Zimbabwean", "1931", "1998"),
    "Bernard Matemera":        ("Zimbabwean", "1946", "2002"),
    "Rosario de Velasco":      ("Spanish", "1904", "1991"),
    "Maija Grotell":           ("Finnish-American", "1899", "1973"),
    "Kate B. Sears":           ("American", None, None),
    "Helen West Heller":       ("American", "1885", "1955"),
}

FALLBACK_MEDIA = {
    "oil on canvas":                        "Oil Paint",
    "oil on canvas, gilded":                "Oil Paint",
    "oil on wood":                          "Oil Paint",
    "watercolor on paper":                  "Watercolour",
    "watercolor and gouache on paper":      "Watercolour",
    "ink on paper":                         "Ink",
    "bronze":                               "Bronze",
    "marble":                               "Marble",
    "terracotta":                           "Terracotta",
    "porcelain":                            "Porcelain",
    "gold":                                 "Gold",
    "silver":                               "Silver",
    "limestone":                            "Limestone",
    "wood":                                 "Wood",
    "ivory":                                "Ivory",
    "copper alloy":                         "Copper Alloy",
    "faience":                              "Faience",
    "linen":                                "Linen",
    "papyrus":                              "Papyrus",
}


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def llm_backend() -> str:
    """Return the active backend name based on environment variables."""
    if os.environ.get("OLLAMA_MODEL"):
        return "ollama"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "fallback"


def _ask_ollama(prompt: str, system: str) -> str:
    """Query a local Ollama server. Free, no API key required."""
    import requests
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    host  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    resp = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": full_prompt, "stream": False,
              "options": {"temperature": 0.0, "num_predict": 256}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def _ask_groq(prompt: str, system: str) -> str:
    """Query Groq's free-tier API (OpenAI-compatible)."""
    import requests
    api_key = os.environ["GROQ_API_KEY"]
    model   = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type":  "application/json"},
        json={"model": model, "messages": messages,
              "max_tokens": 256, "temperature": 0.0},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _ask_anthropic(prompt: str, system: str) -> str:
    """Query the Anthropic API (paid)."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    kwargs = {"model": "claude-haiku-4-5-20251001",
              "max_tokens": 256,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text.strip()


def ask_llm(prompt: str, system: str = "") -> str:
    """
    Dispatch to whichever LLM backend is configured.
    Returns an empty string on failure so the caller falls back to lookup tables.
    """
    backend = llm_backend()
    if backend == "fallback":
        return ""
    try:
        if backend == "ollama":
            return _ask_ollama(prompt, system)
        if backend == "groq":
            return _ask_groq(prompt, system)
        if backend == "anthropic":
            return _ask_anthropic(prompt, system)
    except Exception as exc:
        print(f"  [LLM:{backend}] Warning: {exc}", file=sys.stderr)
    return ""


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_uri(name: str) -> str:
    """
    Convert a human-readable name to a URI fragment using the same logic as
    createTitle() in structured_data_mapping.py:
      1. capitalize()              → first char upper, rest lower
      2. strip parenthetical text
      3. remove non-alphanumeric chars (except spaces)
      4. replace spaces with underscores
    """
    name = name.capitalize()
    name = re.sub(r"\(.*?\)", "", name).strip()
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    return name.replace(" ", "_")


def clean_movement(raw: str) -> str:
    """Extract the movement name from a free-text LLM response."""
    raw = raw.strip().strip("\"'.,;")
    # Take the first line / sentence only
    raw = raw.split("\n")[0].split(".")[0].strip()
    # Remove common preamble phrases
    for preamble in [
        "is associated with",
        "was associated with",
        "belongs to",
        "is best known as part of",
        "is a member of",
        "the movement is",
        "movement:",
    ]:
        if preamble in raw.lower():
            raw = raw.lower().split(preamble)[-1].strip()
    return raw.title() if raw else ""


def clean_nationality(raw: str) -> str:
    """Extract a single nationality word/phrase from an LLM response."""
    raw = raw.strip().strip("\"'.,;")
    raw = raw.split("\n")[0].split(".")[0].strip()
    for preamble in ["nationality:", "their nationality is", "was", "is"]:
        if raw.lower().startswith(preamble):
            raw = raw[len(preamble):].strip()
    return raw.title() if raw else ""


def clean_medium(raw: str) -> str:
    """Extract the primary medium label from an LLM response."""
    raw = raw.strip().strip("\"'.,;")
    raw = raw.split("\n")[0].split(".")[0].strip()
    for preamble in ["primary medium:", "the primary medium is", "medium:"]:
        if raw.lower().startswith(preamble):
            raw = raw[len(preamble):].strip()
    return raw.title() if raw else ""


# ---------------------------------------------------------------------------
# Gap fixes
# ---------------------------------------------------------------------------

def fix_O1_gender(g: Graph, data_path: str = "data.json") -> int:
    """
    Gap O1 — Add myont:hasGender triples from data.json.
    This is a code fix (no RAG required): the field exists in the source
    data but was never mapped in structured_data_mapping.py.
    Returns the number of triples added.
    """
    print("\n[Gap O1] Adding hasGender property from data.json ...")
    if not os.path.exists(data_path):
        print(f"  data.json not found at {data_path}, skipping.")
        return 0

    with open(data_path) as f:
        records = json.load(f)

    added = 0
    for rec in records:
        gender = rec.get("artist_gender", "").strip()
        name   = rec.get("artist", "").strip()
        if not gender or not name:
            continue
        artist_uri = MYONT[safe_uri(name)]
        # Only add if the artist exists in the graph (check both type assertions)
        exists = any(True for _ in g.triples((artist_uri, RDF.type, None)))
        if exists:
            if (artist_uri, MYONT.hasGender, None) not in g:
                g.add((artist_uri, MYONT.hasGender, Literal(gender, datatype=XSD.string)))
                added += 1

    # Also declare the property in the ontology if not already present
    if (MYONT.hasGender, RDF.type, OWL.DatatypeProperty) not in g:
        g.add((MYONT.hasGender, RDF.type, OWL.DatatypeProperty))
        g.add((MYONT.hasGender, RDFS.label, Literal("has gender")))
        g.add((MYONT.hasGender, RDFS.domain, CRM.E21_Person))
        g.add((MYONT.hasGender, RDFS.range,  XSD.string))
        g.add((MYONT.hasGender, RDFS.comment,
               Literal("The gender of an artist as recorded in the source data.")))

    print(f"  Added {added} hasGender triple(s).")
    return added


def fix_O3_museum_location(g: Graph) -> int:
    """
    Gap O3 — Add the missing museum → city location triple.
    The Metropolitan Museum of Art and the myont:New_york instance both
    exist in the KG but are not linked.
    """
    print("\n[Gap O3] Linking Metropolitan Museum of Art to New York ...")

    # Check property exists in ontology
    if (SCHEMA.location, RDF.type, OWL.ObjectProperty) not in g:
        g.add((SCHEMA.location, RDF.type, OWL.ObjectProperty))
        g.add((SCHEMA.location, RDFS.label, Literal("location")))
        g.add((SCHEMA.location, RDFS.domain, SCHEMA.Museum))
        g.add((SCHEMA.location, RDFS.range,  CRM.E53_Place))

    museum_uri = MYONT.Metropolitan_museum_of_art
    city_uri   = MYONT.New_york

    if (museum_uri, SCHEMA.location, city_uri) not in g:
        g.add((museum_uri, SCHEMA.location, city_uri))
        print("  Added: Metropolitan_museum_of_art schema:location New_york")
        return 1

    print("  Triple already present, skipping.")
    return 0


def fix_O5_painter_sculptor_typing(g: Graph) -> int:
    """
    Gap O5 — Explicitly assert rdf:type myont:Painter / myont:Sculptor.
    The defined classes exist as OWL restrictions but no reasoner is run,
    so SPARQL cannot retrieve them. This step materialises the inferences.
    """
    print("\n[Gap O5] Asserting explicit Painter/Sculptor rdf:type triples ...")

    sparql_painters = """
    PREFIX myont: <https://ontologeez/>
    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist WHERE {
        ?artwork rdf:type myont:Painting .
        ?artwork myont:createdBy ?artist .
    }
    """
    sparql_sculptors = """
    PREFIX myont: <https://ontologeez/>
    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist WHERE {
        ?artwork rdf:type myont:Sculpture .
        ?artwork myont:createdBy ?artist .
    }
    """

    added = 0
    for artist_uri, in g.query(sparql_painters):
        if (artist_uri, RDF.type, MYONT.Painter) not in g:
            g.add((artist_uri, RDF.type, MYONT.Painter))
            added += 1

    for artist_uri, in g.query(sparql_sculptors):
        if (artist_uri, RDF.type, MYONT.Sculptor) not in g:
            g.add((artist_uri, RDF.type, MYONT.Sculptor))
            added += 1

    print(f"  Added {added} explicit Painter/Sculptor type triple(s).")
    return added


# ---------------------------------------------------------------------------
# RAG gaps
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a concise art history assistant. "
    "Answer with a single short phrase — no extra explanation, no full sentences."
)


def rag_O2_artistic_movements(g: Graph) -> int:
    """
    Gap O2 — Add myont:ArtisticMovement class and
    myont:associatedWithMovement links via RAG.

    For each artist in the KG, the system:
      1. Retrieves their name, nationality, birth year, and artwork titles.
      2. Verbalises this context into a natural language prompt.
      3. Asks the LLM which artistic movement they are associated with.
      4. Adds the triple and tags it as RAG-generated.
    """
    print("\n[Gap O2] RAG — Artistic movement associations ...")

    # Declare new ontology elements
    if (MYONT.ArtisticMovement, RDF.type, OWL.Class) not in g:
        g.add((MYONT.ArtisticMovement, RDF.type, OWL.Class))
        g.add((MYONT.ArtisticMovement, RDFS.label, Literal("Artistic Movement")))
        g.add((MYONT.ArtisticMovement, RDFS.comment,
               Literal("A named artistic movement, school, or style (e.g. Impressionism).")))

    if (MYONT.associatedWithMovement, RDF.type, OWL.ObjectProperty) not in g:
        g.add((MYONT.associatedWithMovement, RDF.type, OWL.ObjectProperty))
        g.add((MYONT.associatedWithMovement, RDFS.label, Literal("associated with movement")))
        g.add((MYONT.associatedWithMovement, RDFS.domain, MYONT.Artist))
        g.add((MYONT.associatedWithMovement, RDFS.range,  MYONT.ArtisticMovement))

    # Retrieve artist context from the KG
    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist ?name ?nationality ?born WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        OPTIONAL { ?artist myont:hasNationality ?nationality }
        OPTIONAL { ?artist myont:bornOn ?born }
    }
    """

    # Gather artwork titles per artist for context
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
    artist_titles: dict[str, list[str]] = {}
    for row in g.query(title_sparql):
        artist_titles.setdefault(str(row.name), []).append(str(row.title))

    added = 0
    use_llm = llm_backend() != "fallback"

    for row in g.query(sparql):
        artist_uri  = row.artist
        name        = str(row.name)
        nationality = str(row.nationality) if row.nationality else ""
        born        = str(row.born)[:4]    if row.born        else ""

        # Skip if already has a movement
        if (artist_uri, MYONT.associatedWithMovement, None) in g:
            continue

        # --- Retrieve answer ---
        movement = ""

        if use_llm:
            titles = artist_titles.get(name, [])[:5]
            titles_text = ", ".join(f'"{t}"' for t in titles) if titles else "unknown"
            nat_text  = f"nationality {nationality}" if nationality else ""
            born_text = f"born {born}"               if born        else ""
            context   = ", ".join(filter(None, [nat_text, born_text]))
            context   = f" ({context})" if context else ""
            prompt = (
                f"Artist: {name}{context}. "
                f"Representative works: {titles_text}. "
                f"What single artistic movement or style is this artist most associated with?"
            )
            raw = ask_llm(prompt, system=SYSTEM_PROMPT)
            movement = clean_movement(raw)
            time.sleep(0.1)   # respect rate limit

        # Fallback (names in KG are lowercase; match case-insensitively)
        if not movement:
            name_lower = name.lower()
            for k, v in FALLBACK_MOVEMENTS.items():
                if k.lower() == name_lower:
                    movement = v
                    break

        if not movement:
            continue

        # --- Add triples ---
        movement_uri = MYONT[safe_uri(movement)]
        if (movement_uri, RDF.type, MYONT.ArtisticMovement) not in g:
            g.add((movement_uri, RDF.type, MYONT.ArtisticMovement))
            g.add((movement_uri, RDFS.label, Literal(movement)))

        g.add((artist_uri, MYONT.associatedWithMovement, movement_uri))
        g.add((artist_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        added += 1
        print(f"  {name} → {movement}")

    print(f"  Added {added} associatedWithMovement triple(s).")
    return added


def rag_I1_I2_biographical(g: Graph, data_path: str = "data.json") -> int:
    """
    Gaps I1 & I2 — Fill missing artist nationality and birth/death dates via RAG.

    For each artist missing nationality or dates:
      1. Retrieve existing context from the KG (name, known artworks, culture).
      2. Ask the LLM to suggest the missing value.
      3. Add triple and tag as RAG-generated.
    """
    print("\n[Gap I1/I2] RAG — Missing artist nationality and dates ...")

    # Declare ragGenerated annotation property
    if (MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty) not in g:
        g.add((MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty))
        g.add((MYONT.ragGenerated, RDFS.label, Literal("RAG generated")))
        g.add((MYONT.ragGenerated, RDFS.comment,
               Literal("True if this triple was generated by the RAG system rather than from the "
                        "structured data pipeline.")))

    sparql = """
    PREFIX myont:  <https://ontologeez/>
    PREFIX schema: <https://schema.org/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?artist ?name ?nationality ?born ?died WHERE {
        ?artist rdf:type myont:Artist .
        ?artist schema:name ?name .
        OPTIONAL { ?artist myont:hasNationality ?nationality }
        OPTIONAL { ?artist myont:bornOn ?born }
        OPTIONAL { ?artist myont:diedOn ?died }
    }
    """

    use_llm = llm_backend() != "fallback"
    added   = 0

    for row in g.query(sparql):
        artist_uri  = row.artist
        name        = str(row.name)
        nationality = str(row.nationality) if row.nationality else None
        born        = str(row.born)[:4]    if row.born        else None
        died        = str(row.died)[:4]    if row.died        else None

        # ---- Nationality (Gap I1) ----------------------------------------
        if not nationality:
            nat = ""

            if use_llm:
                prompt = (
                    f"What is the nationality of the artist named '{name}'? "
                    "Reply with a single nationality word or short phrase only."
                )
                raw = ask_llm(prompt, system=SYSTEM_PROMPT)
                nat = clean_nationality(raw)
                time.sleep(0.1)

            if not nat:
                name_lower = name.lower()
                fallback = next(
                    (v for k, v in FALLBACK_NATIONALITIES.items() if k.lower() == name_lower),
                    None
                )
                if fallback:
                    nat = fallback[0]

            if nat:
                g.add((artist_uri, MYONT.hasNationality,
                        Literal(nat, datatype=XSD.string)))
                g.add((artist_uri, MYONT.ragGenerated,
                        Literal(True, datatype=XSD.boolean)))
                print(f"  {name} → nationality: {nat}")
                added += 1

        # ---- Birth / death dates (Gap I2) -----------------------------------
        if not born or not died:
            fb = FALLBACK_NATIONALITIES.get(name)
            llm_born, llm_died = None, None

            if use_llm and (not born or not died):
                prompt = (
                    f"For the artist '{name}', provide their birth year and death year "
                    "in the format BORN:YYYY DIED:YYYY. "
                    "Use '?' for unknown. Example: BORN:1840 DIED:1926"
                )
                raw = ask_llm(prompt, system=SYSTEM_PROMPT)
                m_born = re.search(r"BORN:(\d{4})", raw)
                m_died = re.search(r"DIED:(\d{4})", raw)
                llm_born = m_born.group(1) if m_born else None
                llm_died = m_died.group(1) if m_died else None
                time.sleep(0.1)

            # Fallback
            name_lower = name.lower()
            fb = next(
                (v for k, v in FALLBACK_NATIONALITIES.items() if k.lower() == name_lower),
                None
            )
            if not llm_born and fb and fb[1]:
                llm_born = fb[1]
            if not llm_died and fb and fb[2]:
                llm_died = fb[2]

            if not born and llm_born:
                g.add((artist_uri, MYONT.bornOn,
                        Literal(llm_born, datatype=XSD.gYear)))
                g.add((artist_uri, MYONT.ragGenerated,
                        Literal(True, datatype=XSD.boolean)))
                print(f"  {name} → bornOn: {llm_born}")
                added += 1

            if not died and llm_died:
                g.add((artist_uri, MYONT.diedOn,
                        Literal(llm_died, datatype=XSD.gYear)))
                g.add((artist_uri, MYONT.ragGenerated,
                        Literal(True, datatype=XSD.boolean)))
                print(f"  {name} → diedOn: {llm_died}")
                added += 1

    print(f"  Added {added} biographical triple(s).")
    return added


def rag_O4_medium_structure(g: Graph) -> int:
    """
    Gap O4 — Create structured myont:Medium instances from mediumDescription strings.

    For each unique mediumDescription value in the KG:
      1. Ask the LLM: "What is the primary medium in '<description>'?"
      2. Create a myont:Medium instance with that label.
      3. Link artworks to Medium via myont:hasMedium.
      4. Tag as RAG-generated.
    """
    print("\n[Gap O4] RAG — Structured Medium instances from mediumDescription ...")

    # Declare new ontology elements
    if (MYONT.Medium, RDF.type, OWL.Class) not in g:
        g.add((MYONT.Medium, RDF.type, OWL.Class))
        g.add((MYONT.Medium, RDFS.label, Literal("Medium")))
        g.add((MYONT.Medium, RDFS.comment,
               Literal("A structured representation of the primary material or technique "
                        "used to create an artwork.")))

    if (MYONT.hasMedium, RDF.type, OWL.ObjectProperty) not in g:
        g.add((MYONT.hasMedium, RDF.type, OWL.ObjectProperty))
        g.add((MYONT.hasMedium, RDFS.label, Literal("has medium")))
        g.add((MYONT.hasMedium, RDFS.domain, CRM.E22_Human_Made_Object))
        g.add((MYONT.hasMedium, RDFS.range,  MYONT.Medium))

    sparql = """
    PREFIX myont: <https://ontologeez/>
    SELECT DISTINCT ?artwork ?desc WHERE {
        ?artwork myont:mediumDescription ?desc .
    }
    """

    use_llm   = llm_backend() != "fallback"
    desc_cache: dict[str, str] = {}   # desc → medium label
    added = 0

    for row in g.query(sparql):
        artwork_uri = row.artwork
        desc        = str(row.desc).strip().lower()

        # Skip if already linked
        if (artwork_uri, MYONT.hasMedium, None) in g:
            continue

        if desc not in desc_cache:
            medium_label = ""

            if use_llm:
                prompt = (
                    f"Medium description: '{desc}'. "
                    "What is the single primary medium or material? "
                    "Reply with a short label only, e.g. 'Oil Paint', 'Bronze', 'Watercolour'."
                )
                raw = ask_llm(prompt, system=SYSTEM_PROMPT)
                medium_label = clean_medium(raw)
                time.sleep(0.05)

            if not medium_label:
                # Try exact or prefix match in fallback table
                for key, val in FALLBACK_MEDIA.items():
                    if desc.startswith(key) or key in desc:
                        medium_label = val
                        break

            desc_cache[desc] = medium_label

        medium_label = desc_cache[desc]
        if not medium_label:
            continue

        medium_uri = MYONT[safe_uri(medium_label)]
        if (medium_uri, RDF.type, MYONT.Medium) not in g:
            g.add((medium_uri, RDF.type, MYONT.Medium))
            g.add((medium_uri, RDFS.label, Literal(medium_label)))

        g.add((artwork_uri, MYONT.hasMedium, medium_uri))
        g.add((artwork_uri, MYONT.ragGenerated, Literal(True, datatype=XSD.boolean)))
        added += 1

    print(f"  Added {added} hasMedium triple(s) across {len(desc_cache)} unique descriptions.")
    return added


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_rag_pipeline(input_ttl: str, output_ttl: str, data_json: str) -> None:
    print("=" * 60)
    print("RAG Knowledge Graph Completion Pipeline")
    print("=" * 60)
    print(f"Input  : {input_ttl}")
    print(f"Output : {output_ttl}")
    print(f"Data   : {data_json}")
    backend = llm_backend()
    backend_label = {
        "ollama":    f"Ollama (local, model={os.environ.get('OLLAMA_MODEL')})",
        "groq":      f"Groq (free tier, model={os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')})",
        "anthropic": "Anthropic API (paid)",
        "fallback":  "offline (fallback tables)",
    }[backend]
    print(f"LLM    : {backend_label}")
    print()

    # 1. Load the existing KG
    print("Loading knowledge graph ...")
    g = Graph()
    g.parse(input_ttl, format="turtle")
    g.bind("myont",  MYONT)
    g.bind("schema", SCHEMA)
    g.bind("crm",    CRM)
    print(f"  {len(g)} triples loaded.\n")

    initial_count = len(g)

    # Declare ragGenerated annotation property early (used by all RAG steps)
    if (MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty) not in g:
        g.add((MYONT.ragGenerated, RDF.type, OWL.AnnotationProperty))
        g.add((MYONT.ragGenerated, RDFS.label, Literal("RAG generated")))
        g.add((MYONT.ragGenerated, RDFS.comment,
               Literal("True if this triple was generated by the RAG system rather than from "
                        "the structured data pipeline.")))

    # 2. Code fixes (no LLM required)
    fix_O1_gender(g, data_json)
    fix_O3_museum_location(g)
    fix_O5_painter_sculptor_typing(g)

    # 3. RAG gaps (LLM with fallback)
    rag_O2_artistic_movements(g)
    rag_I1_I2_biographical(g, data_json)
    rag_O4_medium_structure(g)

    # 4. Serialise
    final_count = len(g)
    added_total = final_count - initial_count

    print(f"\n{'=' * 60}")
    print(f"Pipeline complete.")
    print(f"  Triples before : {initial_count}")
    print(f"  Triples after  : {final_count}")
    print(f"  Triples added  : {added_total}")
    print(f"  Output file    : {output_ttl}")

    g.serialize(destination=output_ttl, format="turtle")
    print(f"  Saved successfully.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG-based KG completion pipeline.")
    parser.add_argument("--input",  default="art_and_museum_ontology.ttl",
                        help="Input Turtle file (default: art_and_museum_ontology.ttl)")
    parser.add_argument("--output", default="rag_output.ttl",
                        help="Output Turtle file (default: rag_output.ttl)")
    parser.add_argument("--data",   default="data.json",
                        help="Structured data JSON used for code fixes (default: data.json)")
    args = parser.parse_args()

    run_rag_pipeline(args.input, args.output, args.data)
