# Running the Project

1. Run the pipeline to generate the knowledge graph (art_and_museum_ontology.ttl): `python main.py`
2. Run the rag system to generate an updated knowledge graph (rag_output.ttl): `python rag_system.py`
3. To run the evaluation script: `python eval.py`

# Pipeline overview

1. Populate data from structured data source into `data.json` file via `load_data.py`
2. Construct ontology using `ontology_generation.py`
3. Populate instances for the knowledge graph from structured and unstructured data sources via `structured_data_mapping.py` and `llm_pipeline_knowledge_eng.py`
4. Serialise graph into Turtle format via `main.py`
5. Run RAG system via `rag_system.py` to resolve ontology and instance gaps, producing `rag_output.ttl`
6. Evaluate knowledge graph using `eval.py`

# Setup Instructions

1. Clone the repository: `git clone https://github.com/katiepreed/KE-COURSEWORK-2.git`
2. Cd into repo: `cd KE-COURSEWORK-2`
3. Create virtual environment: `python -m venv venv`
4. Activate virtual environment:
   - macOS: `source venv/bin/activate`
   - windows: `venv\Scripts\activate`
5. Install Python dependencies: `pip install -r requirements.txt`
6. Download spaCy language model: `python -m spacy download en_core_web_sm`
7. Download and install Ollama from https://ollama.com/download
8. Pull the Llama model: `ollama pull llama3`
9. Set the model environment variable:
   - macOS: `export OLLAMA_MODEL=llama3`
   - windows: `set OLLAMA_MODEL=llama3`

# Files

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

# Tech stack used in the project

- Python 3
- Requests
- RDFLib
- JSON
- BeautifulSoup
- spaCy
- REBEL (Babelscape/rebel-large)
- Ollama/Llama 3
- owlready2/HermiT
- owlrl
