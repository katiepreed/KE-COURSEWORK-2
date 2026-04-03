import re
from rdflib import Literal

def createTitle(title):
    clean = re.sub(r"\(.*?\)", "", title).strip()      
    clean = re.sub(r"[^a-zA-Z0-9 ]", "", clean)  
    return clean.replace(" ", "_")   

def cleanString(word):
    return re.sub(r"[^a-zA-Z0-9 ]", "", word)  


mediums = {
    "stone": ["stone", "marble", "stoneware"],
    "clay": ["clay", "terracotta", "pottery"],
    "china": ["china", "faience", "porcelain"],
    "wood": ["wood", "mahogany", "maple", "pine"],
    "metal": ["metal", "steel", "gold", "brass", "bronze"],
    "gemstones": ["gemstone", "rubies", "diamonds", "emerald", "sapphires"],
    "glass": ["glass"],
    "ink": ["ink"],
    "oil": ["oil"],
    "watercolor": ["watercolor"],
    "fresco": ["fresco"],
    "pastel": ["pastel"],
}

themes = {
    "nature": ["nature", "flower", "tree", "plant"],
    "animal": ["animal", "cat", "dog", "horse"],
    "religion": ["religion", "god", "biblical"],
    "mythology": ["myth", "allegory"],
}

def setTheme(subject, title, med_description, objectName, g, ONT):
    title_lower = title.lower()
    med_lower = med_description.lower()
    obj_lower = objectName.lower()
    for category, keywords in themes.items():
        for word in keywords:
            if word in title_lower or word in med_lower or word in obj_lower:
                g.add((subject, ONT.theme, Literal(category)))
                break


def setMedium(subject, title, med_description, objectName, g, ONT):
    title_lower = title.lower()
    med_lower = med_description.lower()
    obj_lower = objectName.lower()
    for category, keywords in mediums.items():
        for word in keywords:
            if word in title_lower or word in med_lower or word in obj_lower:
                g.add((subject, ONT.medium, Literal(category)))
                break  
