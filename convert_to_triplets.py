import json
from rdflib import Graph, Literal, Namespace, URIRef, RDF
from rdflib import RDFS
from clean_data import createTitle, cleanString, setTheme, setMedium

ONT = Namespace("http://ontologeez/")

g = Graph()
g.bind("ont", ONT)

with open("data.json", "r") as f:
    data = json.load(f)

# create the class
g.add((ONT.Artwork, RDF.type, RDFS.Class))

# list of predicates
fields = {
    "object_id": ONT.hasObjectId,
    "title": ONT.hasTitle,
    "object_name": ONT.isObjectType,
    "culture": ONT.hasCulture,
    "medium": ONT.hasDescription,
    "period": ONT.hasPeriod,
    "artist": ONT.createdByArtist,
    "country": ONT.originatedInCountry,
    "city": ONT.originatedInCity,
    "region": ONT.originatedInRegion,
    "begin_date": ONT.startOfCreation,
    "end_date": ONT.creationFinishedDate,
    "gallery_number": ONT.belongsToGalleryID,
    "artist_nationality": ONT.artistNationality,
    "artist_begin_date": ONT.artistBirthDate,
}

tracker = set()

# convert each data point into an rdf triples 
for item in data:
    title = item.get("title") or ""
    medium = item.get("medium") or ""
    objectName = item.get("object_name") or ""

    if title in tracker: 
        continue

    tracker.add(title)

    identifier = createTitle(title)
    subject = ONT[f"artwork/{identifier}_{item['object_id']}"]
    
    g.add((subject, RDF.type, ONT.Artwork))

    for key, predicate in fields.items():
        value = item.get(key, "")
        if value:
            g.add((subject, predicate, Literal(value)))

    setTheme(subject, title, medium, objectName, g, ONT)
    setMedium(subject, title, medium, objectName, g, ONT)

# save as a turtle file 
g.serialize(destination="data.ttl", format="turtle")