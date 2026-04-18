import time
import os
from owlready2 import (get_ontology, sync_reasoner_hermit, default_world, World)
from rdflib import Graph 
import owlrl

OWL_FILE = "art_and_museum_ontology_eval.owl"
TTL_FILE = "art_and_museum_ontology.ttl"

g = Graph()
g.parse(TTL_FILE, format="turtle")
g.serialize(OWL_FILE, format="xml")

COMPETENCY_QUERIES = [
    (
        "1. Which artworks were created by a French artist?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artworkName ?artistName
        WHERE {
            ?artwork myont:createdBy ?artist .
            ?artist myont:hasNationality ?nat .
            ?artwork schema:name ?artworkName .
            ?artist schema:name ?artistName .
            FILTER(regex(?nat, "french", "i"))
        }
        """
    ),
    (
        "2. Which artworks were made using bronze?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artworkName ?medium
        WHERE {
            ?artwork myont:mediumDescription ?medium .
            ?artwork schema:name ?artworkName .
            FILTER(regex(?medium, "bronze", "i"))
        }
        """
    ),
    (
        "3. Which artworks have a horse theme?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?artworkName
        WHERE {
            ?artwork myont:hasTheme myont:Horse .
            ?artwork schema:name ?artworkName .
        }
        """
    ),
    (
        "4. Which artworks were created in Egypt?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?artworkName
        WHERE {
            ?artwork schema:locationCreated myont:Egypt .
            ?artwork schema:name ?artworkName .
        }
        """
    ),
    (
        "5. Which artists were born after 1800?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artist ?birthYear
        WHERE {
            ?artist a myont:Artist .
            ?artist myont:bornOn ?birthYear .
            ?artist schema:name ?artistName .
            FILTER(?birthYear > 1800)
        }
        """
    ),
    (
        "6. Which artworks are displayed in the Egyptian Art?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?artworkName
        WHERE {
            ?artwork myont:displayedInDepartment myont:Egyptian_art .
            ?artwork schema:name ?artworkName .
        }
        """
    ),
    (
        "7. Which artworks were made during the New Kingdom period?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?artworkName ?period
        WHERE {
            ?artwork myont:hasPeriod ?period .
            ?artwork schema:name ?artworkName .
            FILTER(regex(?period, "new kingdom", "i"))
        }
        """
    ),
    (
        "8. Which artworks have both a flower theme and were made using oil on canvas?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?artworkName ?medium
        WHERE {
            ?artwork myont:hasTheme myont:Flower .
            ?artwork myont:mediumDescription ?medium .
            ?artwork schema:name ?artworkName .
            FILTER(regex(?medium, "oil on canvas", "i"))
        }
        """
    ),
    (
        "9. Which Dutch artists have artworks displayed in the European Paintings department?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artist ?artistName
        WHERE {
            ?artwork myont:createdBy ?artist .
            ?artwork myont:displayedInDepartment myont:European_paintings .
            ?artist myont:hasNationality ?nat .
            ?artist schema:name ?artistName .
            FILTER(regex(?nat, "dutch", "i"))
        }
        """
    ),
    (
        "10. Which artworks were created in Mesopotamia and have an animal theme?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artwork ?theme 
        WHERE {
            ?artwork schema:locationCreated myont:Mesopotamia .
            ?artwork myont:hasTheme ?theme .
            ?theme a myont:AnimalTheme .
        }
        """
    ),
    (
        "11. Which Sculptures made from metal materials (gold, bronze, brass) were created in a specific country or region?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?medium ?locationName
        WHERE {
            ?object a myont:Sculpture . 
            ?object myont:mediumDescription ?medium .
            ?object schema:name ?objectName .
            ?object schema:locationCreated ?location .
            ?location schema:name ?locationName .
            FILTER(
                regex(?medium, "gold", "i") ||
                regex(?medium, "bronze", "i") ||
                regex(?medium, "brass", "i")
            )
        }
        """
    ),
    (
        "12. Which Ceramics were created during a specific creation period (Tang Dynasty, Ptolemaic Period)?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?ceramic ?ceramicName ?period
            WHERE {
            ?ceramic a myont:Ceramic .
            ?ceramic myont:hasPeriod ?period .
            ?ceramic schema:name ?ceramicName .
            FILTER(
                regex(?period, "tang dynasty", "i") ||
                regex(?period, "ptolemaic", "i") 
            )
        }
        """
    ),
    (
        "13. Which Jewellery objects are made from gemstone materials (gold, emerald, ruby, sapphire, diamond)?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?jewellery ?jewelleryName ?medium
        WHERE {
            ?jewellery a myont:Jewellery .
            ?jewellery myont:mediumDescription ?medium .
            ?jewellery schema:name ?jewelleryName .
            FILTER(
                regex(?medium, "gold", "i") ||
                regex(?medium, "emerald", "i") ||
                regex(?medium, "ruby", "i") ||
                regex(?medium, "sapphire", "i") ||
                regex(?medium, "diamond", "i") 
            )
        }
        """
    ),
    (
        "14. Which Paintings were created using watercolour, ink, or oil and depict an animal theme?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?painting ?paintingName ?medium ?themeName
        WHERE {
            ?painting a myont:Painting .
            ?painting myont:mediumDescription ?medium .
            ?painting myont:hasTheme ?theme .
            ?theme a myont:AnimalTheme .
            ?painting schema:name ?paintingName .
            ?theme schema:name ?themeName .
            FILTER(
                regex(?medium, "watercolor", "i") ||
                regex(?medium, "ink", "i") ||
                regex(?medium, "oil", "i")
            )
        }
        """
    ),
    (
        "15. Which Human Made Objects were created in a specific country or region (Iran, Iraq, Syria)?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?locationName
        WHERE {
            ?object schema:locationCreated ?location .
            ?object schema:name ?objectName .
            ?location schema:name ?locationName .
            FILTER(
                regex(?locationName, "^iran$", "i") ||
                regex(?locationName, "^iraq$", "i") ||
                regex(?locationName, "^syria$", "i")
            )
        }
        """
    ),
    (
        "16. Which Human Made Objects were created in a specific city (Constantinople, Nishapur, New York)?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?cityName
        WHERE {
            ?object schema:locationCreated ?city .
            ?city a myont:City .
            ?object schema:name ?objectName .
            ?city schema:name ?cityName .
            FILTER(
                regex(?cityName, "constantinople", "i") ||
                regex(?cityName, "nishapur", "i") ||
                regex(?cityName, "new york", "i")
            )
        }
        """
    ),
    (
        "17. Which artists were born before a 1800 and have Human Made Objects displayed in the MET museum?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?artist ?artistName ?birthYear
        WHERE {
            ?artist a myont:Artist .
            ?artist myont:bornOn ?birthYear .
            ?artist schema:name ?artistName .
            ?artwork myont:createdBy ?artist .
            ?artwork myont:displayedBy myont:Metropolitan_museum_of_art_new_york_ny .
            FILTER(?birthYear < 1800)
        }
        """
    ),
    (
        "18. Which Human Made Objects were created during the imperial period with roman culture?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?period ?culture
        WHERE {
            ?object myont:hasPeriod ?period .
            ?object myont:hasCulture ?culture .
            ?object schema:name ?objectName .
            FILTER(regex(?culture, "roman", "i"))
            FILTER(regex(?period, "imperial", "i"))
        }
        """
    ),
    (
        "19. Which Human Made Objects depict a religious theme?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?themeName
        WHERE {
            ?object myont:hasTheme ?theme .
            ?theme a myont:ReligiousTheme .
            ?object schema:name ?objectName .
            ?theme schema:name ?themeName .
        }
        """
    ),
    (
        "20. Which Human Made Objects created by French artists depict a mythological theme and are displayed in the European Paintings department?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT Distinct ?object ?objectName ?artistName ?themeName
        WHERE {
            ?object myont:createdBy ?artist .
            ?object myont:hasTheme ?theme .
            ?object myont:displayedInDepartment myont:European_paintings .
            ?object schema:name ?objectName .
            ?artist myont:hasNationality ?nationality .
            ?artist schema:name ?artistName .
            ?theme a myont:MythologicalTheme .
            ?theme schema:name ?themeName .
            FILTER(regex(?nationality, "french", "i"))
        }
        """
    ),
]

def run_sparql_query(g, query):
    results = g.query(query)
    return [
        {str(var): str(row[var]) for var in results.vars if row[var] is not None} for row in results
    ]

def evaluate_consistency(path):
    onto = get_ontology("https://ontologeez/").load(
        fileobj=open(path, "rb")
    )

    sync_reasoner_hermit(infer_property_values=True, debug=0)

    inconsistent = list(default_world.inconsistent_classes()) # returns classes that are unsatisfiable
    classes = list(onto.classes())

    num_individuals = len({
        ind for cls in onto.classes() for ind in cls.instances()
    })

    return {
        "classes": classes,
        "num_classes": len(classes),
        "num_properties": len(list(onto.properties())),
        "num_individuals": num_individuals,
        "inconsistent_classes": [str(c) for c in inconsistent],
        "is_consistent": len(inconsistent) == 0,
    }

def evaluate_inferred_triples(path):
    g = Graph()
    g.parse(path, format="xml") 
    asserted_count = len(g)

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    inferred_count = len(g)

    return {
        "asserted_triples": asserted_count,
        "total_after_reasoning": inferred_count,
        "inferred_triples": inferred_count - asserted_count,
    }

def evaluate_competency_questions(path):
    g = Graph()
    g.parse(path, format="xml")

    results_summary = []

    for label, query in COMPETENCY_QUERIES:
        t0 = time.time()
        res = run_sparql_query(g, query)
        elapsed = time.time() - t0
 
        count = len(res)
        status = "OK" if count > 0 else "NO RESULTS"

        results_summary.append({
            "question": label,
            "result_count": count,
            "status": status,
            "query_time_s": round(elapsed, 4),
        })

    answered = sum(1 for r in results_summary if r["result_count"] > 0)
    total = len(results_summary)

    return {
        "questions": results_summary,
        "answered": answered,
        "total": total,
        "coverage_pct": round(answered / total * 100, 1),
    }

def evaluate_pipeline_performance(path):
    # time to parse
    t0 = time.time()
    g = Graph()
    g.parse(path, format="xml")
    parse_time = time.time() - t0
  
    # time to serialise
    t0 = time.time()
    _ = g.serialize(format="turtle")
    serialize_time = time.time() - t0

    file_size = os.path.getsize(path) / 1024  # KB

    return {
        "file_size_kb": round(file_size, 1),
        "parse_time_s": round(parse_time, 4),
        "serialize_time_s": round(serialize_time, 4),
    }

def format_dict(info):
    for item in info:
        if item == "classes" or item == "questions":
            continue

        print(f"{item}: {info[item]}" )

def show_class_distribution(classes):
    print("Instances per class:")
    class_counts = {}
    for cls in classes:
        count = len(list(cls.instances()))
        class_counts[cls.name] = count

    for name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"{name}: {count}")

def format_cq(cq):
    for q in cq:
        print(f"question: {q['question']}")
        print(f"result count: {q['result_count']}")
        print(f"status: {q['status']}")
        print(f"query time: {q['query_time_s']}")
        print("")

def main():
    consistency_results = evaluate_consistency(OWL_FILE)
    format_dict(consistency_results)
    print("")
    show_class_distribution(consistency_results.pop("classes"))
    print("")

    inferred_triples_results = evaluate_inferred_triples(OWL_FILE)
    format_dict(inferred_triples_results)
    print("")

    cq_results = evaluate_competency_questions(OWL_FILE)
    format_cq(cq_results["questions"])
    format_dict(cq_results)
    print("")

    performance_results = evaluate_pipeline_performance(OWL_FILE)
    format_dict(performance_results)

if __name__ == "__main__":
    main()