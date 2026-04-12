# Setup Instructions

1. Install Python dependencies: `pip install -r requirements.txt`

2. Download spaCy language model: `python -m spacy download en_core_web_sm`

3. Run the pipeline: `python main.py`

## Notes

- This project uses a local open-source language model (**Flan-T5**) via HuggingFace.
- No API keys are required.
- The model will be downloaded automatically on first run.
