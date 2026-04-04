"""
TODO: convert the dates from integers into XSD.date datatype in this file and ontology creation file

Properties to think about: 
- SCHEMA.creator
- CRM.P102_has_title
- MYONT.createdBy
- MYONT.hasCreated
- MYONT.discoveredIn

Deal with unidentified artist
"""
import json
import re
from rdflib import Graph, Literal, Namespace, URIRef, RDF, RDFS, XSD, OWL

def createTitle(title):
    title = title.capitalize()
    clean = re.sub(r"\(.*?\)", "", title).strip()      
    clean = re.sub(r"[^a-zA-Z0-9 ]", "", clean)  
    return clean.replace(" ", "_")   

MYONT  = Namespace("https://example.org/custom#")
SCHEMA = Namespace("https://schema.org/")
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")

g = Graph()
g.parse("art_and_museum_ontology.ttl", format="turtle")
g.bind("myont", MYONT)
g.bind("schema", SCHEMA)
g.bind("crm", CRM)

"""
Only objects that map to a specific class will exist in our ontology. 
"""
OBJECT_TYPE_MAP = {
    "painting":  SCHEMA.Painting,
    "watercolor": SCHEMA.Painting,
    "drawing": SCHEMA.Painting,
    "sculpture": SCHEMA.Sculpture,
    "ceramic": MYONT.Ceramic,
    "figurine": MYONT.Figurine,
    "jewelry": MYONT.Jewellery,
    "brooch": MYONT.Jewellery,
    "necklace": MYONT.Jewellery,
    "locket": MYONT.Jewellery,
    "earring": MYONT.Jewellery,
    "ring": MYONT.Jewellery,
    "scroll": MYONT.Scroll,
    "statue": MYONT.Statue,
    "vase": MYONT.Vase,
}

"""
Not every object in our ontology needs to map to a theme.
"""
THEME_MAP = {
    "animal": MYONT.AnimalTheme,
    "cat": MYONT.AnimalTheme,
    "dog":  MYONT.AnimalTheme,
    "horse": MYONT.AnimalTheme,
    "myth": MYONT.MythologicalTheme,
    "allegory": MYONT.MythologicalTheme,
    "nature": MYONT.NatureTheme,
    "flower": MYONT.NatureTheme,
    "tree": MYONT.NatureTheme,
    "plant": MYONT.NatureTheme,
    "religion": MYONT.ReligiousTheme,
    "god": MYONT.ReligiousTheme,
    "biblical": MYONT.ReligiousTheme,
}

def classify_object(object_name, classification, title, medium):
    """
    Determine the class of the object based on its metadata.
    """
    combined = (object_name + " " + classification + " " + title + " "+ medium).lower()

    for keyword, object_class in OBJECT_TYPE_MAP.items():
        if keyword in combined:
            return object_class
        
    return None


def assign_themes(title, medium, object_name, tags):
    """
    Determine the theme of an object based on its metadata.
    """
    combined = (title + " " + medium + " " + object_name).lower()
    # Also include tags in theme detection
    if tags:
        combined += " " + " ".join(t.lower() for t in tags)

    matched = set()
    for keyword, object_class in THEME_MAP.items():
        name = keyword.capitalize()

        if keyword in combined:
            matched.add(keyword)
            theme_uri = MYONT[name]

            g.add((theme_uri, RDF.type, object_class))
            g.add((theme_uri, SCHEMA.name, Literal(name.lower())))
            g.add((subject, MYONT.hasTheme, theme_uri))
            g.add((theme_uri, MYONT.isThemeOf, subject))

with open("data.json", "r") as f:
    data = json.load(f)

# Track entities so we don't re-create duplicate URIs
seen_artists = {}
seen_departments = {}
seen_museums = {}
seen_countries = {}
seen_cities = {}
seen_regions = {}
seen_mediums = {}

# all artworks in the MET are displayed in new york
new_york = MYONT["New_york"]
g.add((new_york, RDF.type, MYONT.City))
seen_cities[new_york] = True
    
for item in data:
    obj_id       = item.get("object_id")
    title        = item.get("title") or ""
    object_name  = item.get("object_name") or ""
    object_date  = item.get("object_date") or ""
    classification = item.get("classification") or ""
    culture      = item.get("culture") or ""
    medium       = item.get("medium") or ""
    period       = item.get("period") or ""
    begin_date   = item.get("begin_date")
    end_date     = item.get("end_date")
    department   = item.get("department") or ""
    repository   = item.get("repository") or ""
    artist_name  = item.get("artist") or ""
    artist_nat   = item.get("artist_nationality") or ""
    artist_begin = item.get("artist_begin_date") or ""
    artist_end   = item.get("artist_end_date") or ""
    country      = item.get("country") or ""
    city         = item.get("city") or ""
    region       = item.get("region") or ""
    tags         = item.get("tags") or []

    if not title:
        continue

    identifier = createTitle(title)
    subject = MYONT[f"{identifier}_{obj_id}"]

    rdf_class = classify_object(object_name, classification, title, medium)

    # only add objects that belong to a specific class
    if not rdf_class:
        continue

    g.add((subject, SCHEMA.displayLocation, new_york))
    g.add((new_york, SCHEMA.name, Literal("new york")))
    
    # assign object to a class
    g.add((subject, RDF.type, rdf_class))

    g.add((subject, MYONT.hasObjectId, Literal(int(obj_id))))
    g.add((subject, SCHEMA.name, Literal(title.lower())))

    if object_date:
        g.add((subject, SCHEMA.dateCreated, Literal(str(object_date))))

    if culture:
        g.add((subject, MYONT.hasCulture, Literal(culture.lower())))

    if period:
        g.add((subject, MYONT.hasPeriod, Literal(period.lower())))

    if begin_date:
        g.add((subject, MYONT.startDate, Literal(str(begin_date))))

    if end_date:
        g.add((subject, MYONT.endDate, Literal(str(end_date))))

    if medium:
        g.add((subject, MYONT.mediumDescription, Literal(medium.lower())))

    if artist_name and artist_name.lower() != "unidentified artist":
        artist_id = createTitle(artist_name)
        artist_uri = MYONT[artist_id]

        if artist_id not in seen_artists:
            seen_artists[artist_id] = True

            g.add((artist_uri, RDF.type, MYONT.Artist))
            g.add((artist_uri, SCHEMA.name, Literal(artist_name.lower())))

            if artist_nat:
                g.add((artist_uri, MYONT.hasNationality, Literal(artist_nat.lower())))

            if artist_begin:
                g.add((artist_uri, MYONT.bornOn, Literal(str(artist_begin))))

            if artist_end:
                g.add((artist_uri, MYONT.diedOn, Literal(str(artist_end))))

        g.add((subject, MYONT.createdBy, artist_uri))

    if department:
        dept_id = createTitle(department)
        dept_uri = MYONT[dept_id]

        if dept_id not in seen_departments:

            seen_departments[dept_id] = True
            g.add((dept_uri, RDF.type, MYONT.Department))
            g.add((dept_uri, SCHEMA.name, Literal(department.lower())))

            dept_num = item.get("department_id")

            if dept_num:
                g.add((dept_uri, MYONT.hasDepartmentId, Literal(int(dept_num))))

        g.add((subject, MYONT.displayedInDepartment, dept_uri))

    if repository:
        museum_id = createTitle(repository)
        museum_uri = MYONT[museum_id]

        if museum_id not in seen_museums:
            seen_museums[museum_id] = True
            g.add((museum_uri, RDF.type, SCHEMA.Museum))
            g.add((museum_uri, SCHEMA.name, Literal(repository.lower())))
            g.add((museum_uri, MYONT.displays, subject))

        if department:
            dept_id = createTitle(department)
            dept_uri = MYONT[dept_id]
            g.add((museum_uri, MYONT.hasDepartment, dept_uri))
            g.add((dept_uri, MYONT.isDepartmentOf, museum_uri))

        g.add((subject, MYONT.displayedBy, museum_uri))

    if country:
        country_id = createTitle(country)
        country_uri = MYONT[country_id]

        if country_id not in seen_countries:
            seen_countries[country_id] = True
            g.add((country_uri, RDF.type, MYONT.Country))
            g.add((country_uri, SCHEMA.name, Literal(country.lower())))

        g.add((subject, SCHEMA.locationCreated, country_uri))

    if city:
        city_id = createTitle(city)
        city_uri = MYONT[city_id]

        if city_id not in seen_cities:
            seen_cities[city_id] = True
            g.add((city_uri, RDF.type, MYONT.City))
            g.add((city_uri, SCHEMA.name, Literal(city.lower())))

        g.add((subject, SCHEMA.locationCreated, city_uri))
        

    if region:
        region_id = createTitle(region)
        region_uri = MYONT[region_id]

        if region_id not in seen_regions:
            seen_regions[region_id] = True
            g.add((region_uri, RDF.type, MYONT.Region))
            g.add((region_uri, SCHEMA.name, Literal(region.lower())))

        g.add((subject, SCHEMA.locationCreated, region_uri))

    assign_themes(title, medium, object_name, tags)

g.serialize(destination="art_and_museum_ontology.ttl", format="turtle")
print(f"Turtle file updated with {len(data)} records!")