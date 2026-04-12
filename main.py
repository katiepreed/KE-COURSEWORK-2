"""
This is the script responsible for creating the knowledge graph.
"""
from rdflib import Graph
from ontology_generation import build_ontology
from structured_data_mapping import populate_instances
<<<<<<< HEAD
<<<<<<< HEAD
from llm_pipeline_knowledge_eng import extract_from_text
=======
>>>>>>> 457ea15 (Fixed some files)
=======
from llm_pipeline_knowledge_eng import extract_from_text
>>>>>>> 4aeb191 (Adding unstructured data to ontology)

def main():
    g = Graph()

    build_ontology(g)
    print("Ontology built.")

<<<<<<< HEAD
    # populate_instances(g)
=======
    # populate_instances(g)
>>>>>>> 4aeb191 (Adding unstructured data to ontology)
    print("Instances added from structured data source.")

    extract_from_text(g)
    print("Instances added from unstructured data source.")

    g.serialize(destination="art_and_museum_ontology.ttl", format="turtle")
    print(f"Saved to art_and_museum_ontology.ttl ({len(g)} triples)")

if __name__ == "__main__":
    main()