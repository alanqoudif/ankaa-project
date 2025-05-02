import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

# API keys
OPENROUTER_API_KEY = "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"

class LegalTextSplitter(RecursiveCharacterTextSplitter):
    """Custom text splitter for Omani legal documents."""
    def __init__(self, **kwargs):
        super().__init__(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
            **kwargs
        )
    
    def create_documents(self, texts, metadatas=None):
        """Create langchain Document objects from texts."""
        documents = super().create_documents(texts, metadatas)
        # Add section identification logic here in the future
        return documents

def process_law_pdf(file_path):
    """Process a legal PDF document and return langchain Document objects."""
    try:
        doc = fitz.open(file_path)
        text = ""
        
        # Extract text and maintain structure
        for page_num, page in enumerate(doc):
            text += page.get_text()
            text += "\n\n"  # Add extra newlines between pages
        
        # Get document metadata
        metadata = {
            "source": os.path.basename(file_path),
            "title": os.path.basename(file_path).replace(".pdf", ""),
            "page_count": len(doc)
        }
        
        # Close the document
        doc.close()
        
        # Split text into chunks
        splitter = LegalTextSplitter()
        chunks = splitter.split_text(text)
        
        # Create Document objects with source metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy()
            doc_metadata["chunk"] = i
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        
        return documents
    
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def setup_vector_db(documents, persist_directory="./omani_laws"):
    """Set up a vector database from document chunks."""
    try:
        # Ensure the directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Set up embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENROUTER_API_KEY)
        
        # Create vector store
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        
        # Persist to disk
        vector_db.persist()
        
        return vector_db
    
    except Exception as e:
        raise Exception(f"Error setting up vector database: {str(e)}")
