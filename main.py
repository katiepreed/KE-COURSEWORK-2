"""
This is the script responsible for creating the knowledge graph.
"""
from rdflib import Graph
from ontology_generation import build_ontology
from structured_data_mapping import populate_instances

def main():
    g = Graph()

    build_ontology(g)
    print("Ontology built.")

    populate_instances(g)
    print("Instances added.")

    g.serialize(destination="art_and_museum_ontology.ttl", format="turtle")
    print(f"Saved to art_and_museum_ontology.ttl ({len(g)} triples)")

if __name__ == "__main__":
    main()