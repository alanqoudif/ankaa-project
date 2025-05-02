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

def load_legal_documents():
    if st.session_state.data_loaded:
        return
    
    # Create a clean loading UI with progress tracking
    with st.spinner("جاري تحميل المستندات القانونية... برجاء الانتظار"):  # "Loading legal documents... please wait"
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # First, load all PDF files in the legal documents directory
        pdf_files = [os.path.join(LEGAL_FILES_DIR, f) for f in os.listdir(LEGAL_FILES_DIR) if f.endswith('.pdf')]
        
        # Prioritize files that might be related to criminal law
        pdf_files = sorted(pdf_files, key=lambda x: 1 if "جزاء" in x.lower() else 2)
        max_files = min(30, len(pdf_files))  # Process up to 30 files
        
        # Debug log instead of showing user
        logging.info(f"Found {len(pdf_files)} PDF files, processing up to {max_files}")
        
        # Create a status placeholder
        status_text.text(f"تحميل المستندات القانونية (0/{max_files})")
        
        try:
            # Create document objects for each PDF
            all_documents = []
            successful_files = []
            
            for i, pdf_file in enumerate(pdf_files[:max_files]):
                try:
                    # Update progress
                    progress = (i + 1) / max_files
                    progress_bar.progress(progress)
                    status_text.text(f"تحميل: {os.path.basename(pdf_file)} ({i+1}/{max_files})")
                    
                    doc = fitz.open(pdf_file)
                    file_docs = []
                    
                    for page_num, page in enumerate(doc):
                        text = page.get_text()
                        # Skip pages with very little text
                        if len(text.strip()) < 50:
                            continue
                        # Create LangChain document
                        metadata = {
                            "source": pdf_file,
                            "page": page_num
                        }
                        doc_obj = Document(page_content=text, metadata=metadata)
                        file_docs.append(doc_obj)
                    
                    # Only count as successful if we extracted content
                    if file_docs:
                        all_documents.extend(file_docs)
                        successful_files.append(os.path.basename(pdf_file))
                        # Log success to console instead of showing user
                        logging.info(f"✓ Successfully processed {os.path.basename(pdf_file)} - {len(file_docs)} pages")
                    else:
                        # Log failure to console instead of showing user
                        logging.warning(f"⚠ No text content found in {os.path.basename(pdf_file)}")
                    
                    doc.close()
                    
                except Exception as e:
                    # Log error to console instead of showing user
                    logging.error(f"❌ Error processing {os.path.basename(pdf_file)}: {str(e)}")
                    continue
            
            # Check if we have any documents to process
            if all_documents:
                # Update status
                status_text.text("إنشاء قاعدة البيانات الذكية...")
                
                # Split documents into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                
                # Split the documents into chunks
                splits = text_splitter.split_documents(all_documents)
                status_text.text(f"معالجة {len(splits)} مقطع نصي...")
                
                # Create embeddings
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                
                # Create vector store
                status_text.text("إنشاء قاعدة بيانات متجهات النصوص...")
                vector_db = Chroma.from_documents(
                    documents=splits,
                    embedding=embeddings,
                    persist_directory=os.path.join(tempfile.gettempdir(), "chroma_db")
                )
                
                # Persist vector store
                vector_db.persist()
                
                # Create QA chain
                status_text.text("تهيئة نموذج الذكاء الاصطناعي...")
                retriever = vector_db.as_retriever(search_kwargs={"k": 5})
                
                # Create a template for our prompt
                template = """You are an assistant specializing in Omani law. Use the following context to answer the question. If you don't know the answer based on the context, say you don't know and avoid making up an answer.  Try to be detailed and thorough in your response. Always try to cite specific laws, statutes, or legal procedures from Oman when possible. Remember that the context may include Arabic text, which is common in Omani law.

Context: {context}

Question: {question}

Answer:"""
                
                QA_PROMPT = PromptTemplate(
                    template=template,
                    input_variables=["context", "question"]
                )
                
                # Use the OpenRouter API to access the powerful Qwen 1.5 model
                llm = ChatOpenAI(
                    temperature=0.0,
                    model="qwen/qwen1.5-110b",
                    openai_api_key=OPENROUTER_API_KEY,
                    openai_api_base="https://openrouter.ai/api/v1",
                    max_tokens=1000,
                    additional_kwargs={
                        "headers": {
                            "HTTP-Referer": "https://sharia-ai.om",
                            "X-Title": "ShariaAI - Omani Legal Assistant"
                        }
                    }
                )
                
                # Create the QA chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                    chain_type_kwargs={"prompt": QA_PROMPT},
                    return_source_documents=True
                )
                
                # Store in session state - only store the successful files
                st.session_state.documents = successful_files
                st.session_state.vector_db = vector_db
                st.session_state.qa_chain = qa_chain
                st.session_state.data_loaded = True
                
                # Clear the progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show success message with count of successfully loaded documents
                st.success(f"تم تحميل {len(st.session_state.documents)} مستند قانوني بنجاح!")
            else:
                # Clear the progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.error("لم يتم العثور على محتوى في المستندات القانونية.")
                
        except Exception as e:
            # Clear the progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.error(f"خطأ في تحميل المستندات القانونية: {str(e)}")
            logging.error(f"Error loading legal documents: {str(e)}", exc_info=True)

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
    
    # Setup voice input state variables
    if "voice_input_text" not in st.session_state:
        st.session_state.voice_input_text = None
    
    # Layout for the chat input with voice button
    input_col1, input_col2 = st.columns([5, 1])
    
    # Place voice input directly into chat input field
    placeholder = "Ask about Omani law..."
    
    with input_col1:
        # Chat input field with voice transcription if available
        if st.session_state.voice_input_text:
            user_query = st.chat_input(st.session_state.voice_input_text)
            # Clear voice input after user sends or modifies
            if user_query:
                st.session_state.voice_input_text = None
        else:
            user_query = st.chat_input(placeholder)
    
    with input_col2:
        # Voice recording component - now much simpler
        voice_transcription = st.session_state.audio_processor.chat_voice_recorder()
        if voice_transcription:
            st.session_state.voice_input_text = voice_transcription
            st.rerun()
    
    # Process the query (from text input only for now)
    if user_query and (not st.session_state.messages or 
                      user_query != st.session_state.messages[-1].get("content", "") 
                      if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" else True):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            # No need to clear voice input since we're using a different variable now
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(query_to_process)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if st.session_state.qa_chain:
                        try:
                            # Use invoke instead of run to handle multiple return values
                            result = st.session_state.qa_chain.invoke(user_query)
                            
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
    
    # Information panel (moved from sidebar column)
    st.sidebar.info("""
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
