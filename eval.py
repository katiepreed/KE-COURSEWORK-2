import time
import os
from owlready2 import (get_ontology, sync_reasoner_hermit, default_world)
from rdflib import Graph 
import owlrl
import gc
import psutil

OWL_FILE = "rag_output.owl"
TTL_FILE = "rag_output.ttl"

g = Graph()
g.parse(TTL_FILE, format="turtle")
g.serialize(OWL_FILE, format="xml")

COMPETENCY_QUERIES = [
    (
        "1. Which french artist have lived for more than 70 years?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?artistName ?birth ?death ?lifespan

        WHERE {
        ?artist a myont:Artist ;
            myont:bornOn ?birth ;
            myont:diedOn ?death ;
            schema:name  ?artistName ;
            myont:hasNationality ?nationality .

        FILTER(regex(?nationality, "french", "i"))
        BIND((?death - ?birth) AS ?lifespan)
        FILTER(?lifespan > 70)
        }

        ORDER BY DESC(?lifespan)
        """
    ),
    (
        "2. Which artworks have bronze as their primary medium and what theme do they have?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?artwork ?theme
        WHERE {
        ?artwork myont:hasPrimaryMedium myont:Bronze ;
            schema:name ?artworkName ;
            myont:hasTheme ?theme .
        }
        """
    ),
    (
        "3. Which artistic movements include artists of more than one nationality? ",
        """
        PREFIX myont: <https://ontologeez/>

        SELECT ?movement (COUNT(DISTINCT ?nationality) AS ?numNationalities)

        WHERE {
        ?artist a myont:Artist ;
            myont:associatedWithMovement ?movement ;
            myont:hasNationality ?nationality .
        }

        GROUP BY ?movement
        HAVING (COUNT(DISTINCT ?nationality) > 1)
        ORDER BY DESC(?numNationalities)
        """
    ),
    (
        "4. Which artworks were created in Egypt and displayed in Egyptian Art department?",
        """
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?artwork ?artworkName
        WHERE {
        ?artwork schema:locationCreated myont:Egypt ;
            myont:displayedInDepartment myont:Egyptian_Art ;
            schema:name ?artworkName .
        }
        """
    ),
    (
        "5. What medium do artworks with horse themes use in different artistic movements ?",
        """
        PREFIX myont:  <https://ontologeez/>

        SELECT ?movement 
            (COUNT(DISTINCT ?artwork) AS ?numHorseArtworks)
            (GROUP_CONCAT(DISTINCT ?medium; SEPARATOR=", ") AS ?mediaUsed)

        WHERE {
        ?artwork myont:hasTheme myont:Horse ;
            myont:createdBy ?artist ;
            myont:hasPrimaryMedium ?medium .
        ?artist  myont:associatedWithMovement ?movement .
        }

        GROUP BY ?movement
        """
    ),
    (
        "6. What is the most recent artwork in the Greek and Roman art department in the MET museum?",
        """
        SELECT ?artwork ?endDate

        WHERE {
        ?artwork myont:displayedBy myont:Metropolitan_Museum_Of_Art_New_York_Ny ;
            myont:displayedInDepartment ?department ;
            myont:endDate ?endDate ;
            schema:name ?artworkName .
        ?department schema:name ?departmentName .
        FILTER(regex(?departmentName, "greek and roman art", "i"))
        }

        ORDER BY DESC(?endDate)
        LIMIT 1
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
        "9. What is the most common primary medium used within each type of artwork?",
        """
        PREFIX myont: <https://ontologeez/>

        SELECT ?type ?medium ?n

        WHERE {
        {
            SELECT ?type ?medium (COUNT(?artwork) AS ?n)
            WHERE {
            ?artwork a ?type ;
                    myont:hasPrimaryMedium ?medium .
            FILTER(?type IN (myont:Painting, myont:Sculpture, myont:Ceramic, myont:Jewellery))
            }
            GROUP BY ?type ?medium
        }
        {
            SELECT ?type (MAX(?cnt) AS ?maxN)
            WHERE {
            SELECT ?type ?medium (COUNT(?artwork) AS ?cnt)
            WHERE {
                ?artwork a ?type ;
                        myont:hasPrimaryMedium ?medium .
                FILTER(?type IN (myont:Painting, myont:Sculpture, myont:Ceramic, myont:Jewellery))
            }
            GROUP BY ?type ?medium
            }
            GROUP BY ?type
        }
        FILTER(?n = ?maxN)
        }
        ORDER BY ?type
        """
    ),
    (
        "10. Which artworks were created in and displayed in New York?",
        """
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?artwork 
        WHERE {
        ?artwork schema:locationCreated myont:New_York ;
            schema:displayLocation myont:New_York ;
            schema:name ?artworkName .
        }
        """
    ),
    (
        "11. Which departments belong to the Metropolitan Museum and how many artworks do they each display?",
        """
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT ?department(COUNT(DISTINCT ?artwork) AS ?numArtworks)

        WHERE {
        ?department myont:isDepartmentOf myont:Metropolitan_Museum_Of_Art_New_York_Ny ;
            schema:name ?departmentName .
        OPTIONAL {
            ?artwork myont:displayedInDepartment ?department .
        }
        }

        GROUP BY ?department
        ORDER BY DESC(?numArtworks)
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
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?artwork ?artworkName ?countryName
        WHERE {
        ?artwork schema:locationCreated ?location ;
            schema:name ?artworkName .
        ?location myont:locatedIn* ?country .
        FILTER(?country IN (myont:Iran, myont:Iraq, myont:Syria))
        OPTIONAL { ?country schema:name ?countryName . }
        }
        """
    ),
    (
        "16. Which 10 artists have created the most artworks?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT ?artist (COUNT(?artwork) AS ?numArtworks)

        WHERE {
        ?artwork myont:createdBy ?artist .
        }

        GROUP BY ?artist
        ORDER BY DESC(?numArtworks)
        LIMIT 10
        """
    ),
    (
        "17. Which museums are located anywhere in Europe?",
        """
        PREFIX myont: <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT DISTINCT ?museum ?museumName ?place

        WHERE {
        ?museum a myont:Museum ;
            myont:locatedIn+ ?place .

        ?place  a myont:Region .

        FILTER(?place IN (myont:Western_Europe, myont:Eastern_Europe,
            myont:Northern_Europe, myont:Southern_Europe))

        OPTIONAL { ?museum schema:name ?museumName . }
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
        "19. Which female artists have artwork displayed in the Metropolitan Museum?",
        """
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT ?artist (COUNT(DISTINCT ?artwork) AS ?numArtworks)
        WHERE {
        ?artist a myont:Artist ;
                myont:hasGender "female"^^xsd:string .
        ?artwork myont:createdBy    ?artist ;
                myont:displayedBy  myont:Metropolitan_Museum_Of_Art_New_York_Ny .
        }
        GROUP BY ?artist 
        ORDER BY DESC(?numArtworks)
        """
    ),
    (
        "20. Which artworks created by French artists depict a mythological theme and are displayed in the European Paintings department?",
        """
        PREFIX myont:  <https://ontologeez/>
        PREFIX schema: <https://schema.org/>

        SELECT ?artwork

        WHERE {
        ?artwork myont:createdBy ?artist ;
                myont:hasTheme ?theme ;
                myont:displayedInDepartment myont:European_Paintings .

        ?artist myont:hasNationality ?nationality .
        ?theme  a myont:MythologicalTheme .
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
    process = psutil.Process(os.getpid())

    # time and memory to parse
    gc.collect()
    mem_before_parse_mb = process.memory_info().rss / 1024 / 1024
    t0 = time.time()
    g = Graph()
    g.parse(path, format="xml")
    parse_time = time.time() - t0
    mem_after_parse_mb = process.memory_info().rss / 1024 / 1024

    # time and memory to serialise
    gc.collect()
    mem_before_ser_mb = process.memory_info().rss / 1024 / 1024
    t0 = time.time()
    _ = g.serialize(format="turtle")
    serialize_time = time.time() - t0
    mem_after_ser_mb = process.memory_info().rss / 1024 / 1024

    file_size = os.path.getsize(path) / 1024  # KB

    return {
        "file_size_kb":          round(file_size, 1),
        "parse_time_s":          round(parse_time, 4),
        "parse_memory_delta_mb": round(mem_after_parse_mb - mem_before_parse_mb, 3),
        "serialize_time_s":      round(serialize_time, 4),
        "serialize_memory_delta_mb": round(mem_after_ser_mb - mem_before_ser_mb, 3),
        "total_rss_mb":          round(mem_after_ser_mb, 2),
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