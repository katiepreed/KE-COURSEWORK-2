import re
import unicodedata
import urllib.parse
from rdflib import URIRef, Namespace

MYONT  = Namespace("https://ontologeez/")
SCHEMA = Namespace("https://schema.org/")
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")

PREFIX_MAP = {
    "myont":  MYONT,
    "schema": SCHEMA,
    "crm":    CRM,
}

ALIASES = {
    "uk": "United Kingdom",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "drc": "Democratic Republic Of The Congo",
    "holland": "Netherlands",
    "new york city": "New York",
    "nyc": "New York",
    "new york, ny": "New York",
    "london, england": "London",
}

def bind_namespaces(g):
    g.bind("myont",  MYONT)
    g.bind("schema", SCHEMA)
    g.bind("crm",    CRM)

def resolve_alias(name: str) -> str:
    return ALIASES.get(name.strip().lower(), name)

def make_uri(name: str, namespace=MYONT) -> URIRef:
    name = resolve_alias(name)
    name = urllib.parse.unquote(str(name).strip())
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"['\u2019]s\b", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    parts = name.strip().split()
    name = "_".join(word.capitalize() for word in parts)
    return URIRef(str(namespace) + name)