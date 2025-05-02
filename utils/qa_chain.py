from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

# API keys
OPENROUTER_API_KEY = "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"
LLAMAINDEX_API_KEY = "llx-gtcRZJSsolYe3nOrX80tXf5cMySyp2K4KdCd14HbWcTor3jz"

# Define prompt templates
qa_template = """You are ShariaAI, an AI-powered legal assistant specializing in Omani law.
Answer the user's question based on the provided legal context. If the answer cannot be found in the context, 
politely state that you don't have that information rather than making up an answer.

Always cite the specific law, article, or section your information comes from. Format citations as [Law Name, Article X].

QUESTION: {question}
CONTEXT: {context}

ANSWER:"""

qa_prompt = PromptTemplate(
    template=qa_template,
    input_variables=["question", "context"]
)

def create_qa_chain(vector_db, use_openrouter=True):
    """Create a RetrievalQA chain with the given vector database."""
    try:
        # Set up the language model
        if use_openrouter:
            llm = ChatOpenAI(
                openai_api_key=OPENROUTER_API_KEY,
                model="openai/gpt-4o",
                temperature=0,
                max_tokens=2000
            )
        else:
            # Fallback to local model in future implementation
            llm = ChatOpenAI(
                openai_api_key=OPENROUTER_API_KEY,
                model="openai/gpt-3.5-turbo",
                temperature=0,
                max_tokens=2000
            )
        
        # Create the retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": qa_prompt},
            return_source_documents=True
        )
        
        return qa_chain
    
    except Exception as e:
        raise Exception(f"Error creating QA chain: {str(e)}")

def analyze_legal_case(qa_chain, scenario, focus_areas):
    """Analyze a legal case scenario against Omani laws."""
    try:
        analysis_prompt = f"""Analyze this scenario against Omani laws:
        Scenario: {scenario}
        Focus Areas: {', '.join(focus_areas)}
        Output format: 
        [Impact Level]: (High/Medium/Low)
        [Relevant Laws]: List the most relevant laws and articles
        [Recommended Actions]: Suggested next steps based on Omani legal framework"""
        
        result = qa_chain.run(analysis_prompt)
        return result
    
    except Exception as e:
        raise Exception(f"Error analyzing case: {str(e)}")

def compare_legal_provisions(qa_chain, provision1, provision2):
    """Compare two legal provisions and highlight differences."""
    try:
        comparison_prompt = f"""Compare these two legal provisions from Omani law:
        Provision 1: {provision1}
        Provision 2: {provision2}
        
        In your comparison, please address:
        1. The key similarities between the provisions
        2. The notable differences or distinctions
        3. The practical implications of these differences
        4. Any relevant case law or precedents
        
        Format your response clearly with headings for each section."""
        
        result = qa_chain.run(comparison_prompt)
        return result
    
    except Exception as e:
        raise Exception(f"Error comparing provisions: {str(e)}")
