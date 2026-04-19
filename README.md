# Setup Instructions

1. Clone the repository: `git clone https://github.com/katiepreed/KE-COURSEWORK-2.git`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Download spaCy language model: `python -m spacy download en_core_web_sm`
4. Download and install Ollama from https://ollama.com/download
5. Pull the Llama model: `ollama pull llama3`
6. Set the model environment variable:
   - macOS: `export OLLAMA_MODEL=llama3`
   - windows: `set OLLAMA_MODEL=llama3`

# Running the Project

1. Run the pipeline to generate the knowledge graph (art_and_museum_ontology.ttl): `python main.py`
1. Run the rag system to generate an updated knowledge graph (rag_output.ttl): `python rag_system.py`

## Files

Relevant files in the directory:

- `load_data.py`: used to populate the data.json file with structured data. You do not need to run this file. The data has already been populated.
- `ontology_generation.py`: defines OWL classes and properties
- `main.py`: this is the file that will build the ontology and populate instances into the knowledge graph.
- `structured_data_mapping.py`: maps MET API data to RDF triples
- `llm_pipeline_knowledge_eng.py`: extracts rdf triples from unstructured text
- `rag_system.py`: this file reads the art_and_museum_ontology.ttl file and fills ontology and instance gaps, writing the new graph to rag_output.ttl
- `eval.py`: this file runs an evaluation on rag_output.ttl, checking for consistency, inference, sparql and pipeline performance
- `cq.txt`: contains competency questions
- `uri_utils.py`: contains URI construction and API utilities
- `data.json`: contains data from the MET API
