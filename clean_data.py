import re
from rdflib import Literal

def createTitle(title):
    clean = re.sub(r"\(.*?\)", "", title).strip()      
    clean = re.sub(r"[^a-zA-Z0-9 ]", "", clean)  
    return clean.replace(" ", "_")   

def cleanString(word):
    return re.sub(r"[^a-zA-Z0-9 ]", "", word)  

objects = {
    "painting": ["painting", "watercolor", "drawing"],
    "sculpture": ["sculpture"],
    "ceramic": ["ceramic"],
    "figurine": ["figurine"],
    "jewelry": ["brooch", "necklace", "locket", "earring", "jewel", "ring"],
    "scroll": [ "scroll"],
    "statue": ["statue"],
    "vase": ["vase"],
}

themes = {
    "animal": ["animal", "cat", "dog", "horse"],
    "mythology": ["myth", "allegory"],
    "nature": ["nature", "flower", "tree", "plant"],
    "religion": ["religion", "god", "biblical"],
}

def setTheme(subject, title, med_description, objectName, g, ONT):
    title_lower = title.lower()
    med_lower = med_description.lower()
    obj_lower = objectName.lower()
    for category, keywords in themes.items():
        for word in keywords:
            if word in title_lower or word in med_lower or word in obj_lower:
                g.add((subject, ONT.hasTheme, Literal(category)))
                break
