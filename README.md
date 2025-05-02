# ShariaAI - Omani Legal Assistant

![ShariaAI Logo](/Users/faisalalanqoudi/anka-project/pho.png)

ShariaAI is an intelligent legal assistant that helps users navigate Omani laws through natural language interactions. The system provides document search, summarization, comparison, and generation capabilities while strictly adhering to official legal texts.

## Features

- **Legal Document Search**: Upload and parse Omani legal PDFs with semantic search and highlighted excerpts
- **Section Navigator**: Browse laws, articles, and clauses hierarchically with automatic summarization
- **Voice-Activated Comparison**: Transcribe voice queries and compare legal provisions side-by-side
- **Document Factory**: Generate template-based legal documents with custom PDF styling
- **Case Analyzer**: Assess legal impact of scenarios with multi-document citation reports

## Tech Stack

- **Frontend**: Streamlit with custom CSS
- **Document Processing**: PyMuPDF + LangChain
- **Vector Database**: ChromaDB (FAISS as backup)
- **LLM Integration**: OpenRouter API (with local LLM fallback via LlamaIndex)
- **PDF Generation**: WeasyPrint
- **Voice Processing**: Whisper API (Vosk for offline)
- **Authentication**: Supabase (optional)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alanqoudif/ankaa-project.git
   cd ankaa-project
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
ShariaAI/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── data/                  # Legal document storage
├── static/                # CSS and other static files
└── utils/                 # Utility modules
    ├── document_processor.py    # PDF processing and vector storage
    ├── qa_chain.py              # Question answering and analysis
    ├── audio_processor.py       # Voice transcription
    ├── pdf_generator.py         # Document generation
    └── supabase_client.py       # Authentication and storage
```

## API Keys

The application uses the following API keys:
- OpenRouter API for LLM access
- LlamaIndex API for local LLM fallback (optional)
- Supabase for authentication (optional)

To set up your own API keys, modify the relevant constants in the utility modules.

## Development

The project follows a level-based development approach:

1. **Level 1**: Document ingestion and basic Q&A
2. **Level 2**: Section navigation and summarization
3. **Level 3**: Voice-activated comparison
4. **Level 4**: Document generation capabilities
5. **Level 5**: Case analysis and risk assessment

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For any questions or issues, please open an issue on the GitHub repository.
