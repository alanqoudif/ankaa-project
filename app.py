import streamlit as st
import os
import tempfile
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from utils.env_loader import load_env_vars
from utils.section_navigator import SectionNavigator
from utils.audio_processor import AudioProcessor
from utils.legal_comparison import LegalComparison
from utils.case_analyzer import CaseAnalyzer
from utils.document_drafter import DocumentDrafter

# Set page configuration
st.set_page_config(
    page_title="ShariaAI - Omani Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
env_vars = load_env_vars()
OPENROUTER_API_KEY = env_vars["openrouter_api_key"]
LLAMAINDEX_API_KEY = env_vars["llamaindex_api_key"]
LEGAL_FILES_DIR = env_vars["legal_files_dir"]

# Display API key status in sidebar (commented out for security)
# st.sidebar.write(f"OpenRouter API Key: {OPENROUTER_API_KEY[:10]}...")
# st.sidebar.write(f"LlamaIndex API Key: {LLAMAINDEX_API_KEY[:10]}...")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "section_navigator" not in st.session_state:
    st.session_state.section_navigator = SectionNavigator()
if "audio_processor" not in st.session_state:
    st.session_state.audio_processor = AudioProcessor()
if "legal_comparison" not in st.session_state:
    st.session_state.legal_comparison = LegalComparison()
if "case_analyzer" not in st.session_state:
    st.session_state.case_analyzer = CaseAnalyzer()
if "document_drafter" not in st.session_state:
    st.session_state.document_drafter = DocumentDrafter()
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Chat"

# Title and description
st.title("ShariaAI - Omani Legal Assistant")
st.markdown("""
An intelligent legal assistant that helps users navigate Omani laws through natural language interactions.
""")

# Define helper functions
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
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_text(text)
        
        # Create Document objects with source metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy()
            doc_metadata["chunk"] = i
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        
        return documents
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return []

def setup_vector_db(documents, persist_directory="./omani_laws"):
    """Set up a vector database from document chunks."""
    try:
        # Ensure the directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Use HuggingFace embeddings for compatibility
        try:
            # Import HuggingFace embeddings
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # Initialize with a small, fast model
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            
            st.success("Using HuggingFace embeddings for vector database.")
        except Exception as e:
            st.error(f"Error setting up HuggingFace embeddings: {str(e)}")
            return None
        
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
        st.error(f"Error setting up vector database: {str(e)}")
        return None

def create_qa_chain(vector_db):
    """Create a RetrievalQA chain with the given vector database."""
    try:
        # Initialize the language model with OpenRouter API using Qwen model
        llm = ChatOpenAI(
            openai_api_key=OPENROUTER_API_KEY,
            model="qwen/qwen3-235b-a22b:free",  # Using Qwen 23.5B model (free tier)
            temperature=0.1,
            max_tokens=1024,  # Increased token limit for Qwen model
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/alanqoudif/ankaa-project",
                "X-Title": "ShariaAI - Omani Legal Assistant"
            }
        )
        
        # Define prompt template
        qa_template = """You are ShariaAI, an AI-powered legal assistant specializing in Omani law.
        Answer the user's question based on the provided legal context. If the answer cannot be found in the context, 
        politely state that you don't have that information rather than making up an answer.

        Always cite the specific law, article, or section your information comes from. Format citations as [Law Name, Article X].

        QUESTION: {question}
        CONTEXT: {context}

        ANSWER:"""
        
        prompt = PromptTemplate(
            template=qa_template,
            input_variables=["context", "question"]
        )
        
        # Create the chain
        chain_type_kwargs = {"prompt": prompt}
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs=chain_type_kwargs,
            return_source_documents=True,
        )
        
        return qa_chain
        
    except Exception as e:
        st.error(f"Error creating QA chain: {str(e)}")
        return None

# Function to load legal documents from data directory
def load_legal_documents():
    if st.session_state.data_loaded:
        return
    
    with st.spinner("Loading Omani legal documents..."):
        try:
            # Get all PDF files in the legal directory
            pdf_files = [os.path.join(LEGAL_FILES_DIR, f) for f in os.listdir(LEGAL_FILES_DIR) if f.endswith('.pdf')]
            
            if not pdf_files:
                st.error(f"No PDF files found in {LEGAL_FILES_DIR}")
                return
            
            # Process all files in the legal directory
            # First, prioritize loading any criminal/penal code documents
            criminal_law_keywords = ['جزاء', 'جنائي', 'عقوبات', 'penal', 'criminal']
            
            # Sort files to prioritize criminal law documents
            priority_files = []
            regular_files = []
            
            for pdf_file in pdf_files:
                file_name = os.path.basename(pdf_file).lower()
                if any(keyword in file_name for keyword in criminal_law_keywords):
                    priority_files.append(pdf_file)
                else:
                    regular_files.append(pdf_file)
            
            # Combine lists with priority files first
            sorted_pdf_files = priority_files + regular_files
            
            # Process files, loading at least 20 documents or all priority files
            max_docs = 30  # Increased from 5 to 30 for better coverage
            all_documents = []
            
            for pdf_file in sorted_pdf_files[:max_docs]:  # Load more documents
                documents = process_law_pdf(pdf_file)
                if documents:
                    all_documents.extend(documents)
                    st.session_state.documents.append(os.path.basename(pdf_file))
                    
                    # Load document into section navigator as well
                    st.session_state.section_navigator.load_document(pdf_file)
            
            if all_documents:
                # Initialize vector database
                st.session_state.vector_db = setup_vector_db(all_documents)
                
                # Create QA chain
                if st.session_state.vector_db is not None:
                    st.session_state.qa_chain = create_qa_chain(st.session_state.vector_db)
                    st.session_state.data_loaded = True
                    st.success(f"Successfully loaded {len(st.session_state.documents)} legal documents!")
            else:
                st.error("Could not process any legal documents.")
                
        except Exception as e:
            st.error(f"Error loading legal documents: {str(e)}")

# Load legal documents on app startup
load_legal_documents()

# Main layout with sidebar
with st.sidebar:
    st.header("Document Repository")
    
    # Display list of processed documents
    if st.session_state.documents:
        st.subheader("Loaded Legal Documents")
        for doc in st.session_state.documents:
            st.write(f"- {doc}")
    
    # Reload button
    if st.button("Reload Documents"):
        st.session_state.data_loaded = False
        st.session_state.documents = []
        load_legal_documents()

    # Info about documents
    st.subheader("About the Documents")
    st.write("The system is loaded with Omani legal documents for reference.")


# Create tabs for different features
tabs = st.tabs(["Chat", "Section Navigator", "Document Browser", "Provision Comparison", "Case Analysis", "Document Drafter"])

# Tab 1: Chat Interface
with tabs[0]:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Initialize chat transcription if not already done
    if "chat_voice_input" not in st.session_state:
        st.session_state.chat_voice_input = None
    
    # Chat input area with voice recording option
    input_col1, input_col2 = st.columns([5, 1])
    
    with input_col1:
        # Show transcription in the input field if available
        placeholder_text = st.session_state.chat_voice_input if st.session_state.chat_voice_input else "Ask about Omani law..."
        user_query = st.chat_input(placeholder_text)
    
    with input_col2:
        # Voice input button and processing
        chat_transcription = st.session_state.audio_processor.chat_voice_recorder()
        
        # If we have a new transcription, update the chat voice input
        if chat_transcription and chat_transcription != st.session_state.chat_voice_input:
            st.session_state.chat_voice_input = chat_transcription
            st.experimental_rerun()
    
    # Clear transcription if a text query is submitted
    if user_query and st.session_state.chat_voice_input:
        if user_query != st.session_state.chat_voice_input:
            st.session_state.chat_voice_input = None
    
    # Process the query from either text input or voice transcription
    query_to_process = user_query or st.session_state.chat_voice_input
    
    if query_to_process and (not st.session_state.messages or 
                          query_to_process != st.session_state.messages[-1].get("content", "") 
                          if st.session_state.messages[-1]["role"] == "user" else True):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": query_to_process})
            
            # Clear voice input after processing
            st.session_state.chat_voice_input = None
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(query_to_process)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if st.session_state.qa_chain:
                        try:
                            # Use invoke instead of run to handle multiple return values
                            result = st.session_state.qa_chain.invoke(query_to_process)
                            
                            # Extract the answer from the result
                            if isinstance(result, dict) and 'result' in result:
                                response = result['result']
                                
                                # Show source documents if available
                                if 'source_documents' in result and result['source_documents']:
                                    sources = result['source_documents']
                                    response += "\n\n**Sources:**"
                                    for i, doc in enumerate(sources[:3]):  # Show up to 3 sources
                                        source = doc.metadata.get('source', 'Unknown')
                                        response += f"\n- {os.path.basename(source)}"
                            else:
                                response = str(result)
                                
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Error generating response: {str(e)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    else:
                        no_kb_msg = "Please upload a legal document first to enable the knowledge base."
                        st.warning(no_kb_msg)
                        st.session_state.messages.append({"role": "assistant", "content": no_kb_msg})
    
    with chat_col2:
        # Information panel
        st.info("""
        **How to Use:**
        1. Type your question about Omani law
        2. Get answers with citations to relevant laws
        3. Follow up with more questions
        """)

# Tab 2: Section Navigator (Level 2 Feature)
with tabs[1]:
    if st.session_state.data_loaded:
        st.session_state.section_navigator.render_section_navigator()
    else:
        st.warning("Please load documents first to use the Section Navigator.")
        
        # Add a button to manually load documents
        if st.button("Load Documents"):
            load_legal_documents()

# Tab 3: Document Browser
with tabs[2]:
    st.header("Document Browser")
    
    if st.session_state.documents:
        # Display list of loaded documents with more details
        st.subheader("Loaded Legal Documents")
        for i, doc in enumerate(st.session_state.documents):
            with st.expander(f"{i+1}. {doc}"):
                # Get document's root section from section navigator if available
                root = st.session_state.section_navigator.select_document(doc)
                if root:
                    # Display basic document info
                    st.write(f"**Title:** {doc}")
                    st.write(f"**Number of Sections:** {len(root.children)}")
                    
                    # List top-level sections
                    if root.children:
                        st.write("**Main Sections:**")
                        for section in root.children[:5]:  # Show first 5 sections
                            st.write(f"- {section.title}")
                        
                        if len(root.children) > 5:
                            st.write(f"... and {len(root.children) - 5} more sections")
                else:
                    st.write("Document loaded but not indexed for navigation.")
    else:
        st.warning("No documents loaded yet. Please load documents first.")
        
        # Add a button to manually load documents
        if st.button("Load Documents", key="load_docs_browser"):
            load_legal_documents()

# Tab 4: Provision Comparison (Level 3 Feature)
with tabs[3]:
    st.header("Legal Provision Comparison")
    st.write("Compare different legal provisions and see highlighted differences")
    
    if st.session_state.data_loaded:
        # Get PDF document paths for comparison
        pdf_files = [os.path.join(LEGAL_FILES_DIR, f) for f in os.listdir(LEGAL_FILES_DIR) if f.endswith('.pdf')]
        
        # Render the comparison interface
        st.session_state.legal_comparison.render_comparison_interface(pdf_files)
    else:
        st.warning("Please load legal documents first to enable comparison.")
        
        if st.button("Load Documents", key="load_docs_comparison"):
            load_legal_documents()

# Tab 5: Case Analysis (Level 4 Feature)
with tabs[4]:
    st.header("Case Analysis")
    st.write("Analyze legal cases with structured reasoning and step-by-step analysis")
    
    # Render the case analysis interface
    st.session_state.case_analyzer.render_case_analysis_interface()

# Tab 6: Document Drafter (Level 4 Feature)
with tabs[5]:
    st.header("Document Drafter")
    st.write("Generate professional legal documents, letters, and memos")
    
    # Render the document drafter interface
    st.session_state.document_drafter.render_document_drafter_interface()

# Footer
st.markdown("---")
st.markdown("© 2025 ShariaAI - Omani Legal Assistant | Developed with Streamlit")
