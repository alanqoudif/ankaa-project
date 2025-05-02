"""
Legal Comparison module for ShariaAI - Compare legal provisions and highlight differences.
Level 3 Feature: Side-by-section legal provision comparison with difference highlighting
"""
import os
import re
import difflib
import streamlit as st
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
from langchain_openai import ChatOpenAI
from utils.env_loader import load_env_vars

class LegalComparison:
    """Handle comparison between legal provisions with difference highlighting."""
    
    def __init__(self):
        """Initialize the legal comparison module with LLM connection."""
        # Load environment variables
        env_vars = load_env_vars()
        self.openrouter_api_key = env_vars['openrouter_api_key']
        
        # Initialize the language model for intelligent comparison
        self.llm = ChatOpenAI(
            openai_api_key=self.openrouter_api_key,
            model="qwen/qwen3-235b-a22b:free",
            temperature=0.0,  # Keep deterministic for legal analysis
            max_tokens=1500,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/alanqoudif/ankaa-project",
                "X-Title": "ShariaAI - Omani Legal Assistant"
            }
        )
    
    def extract_provision(self, document_path: str, query: str) -> List[Dict[str, str]]:
        """
        Extract legal provisions from a document based on a query.
        
        Args:
            document_path: Path to the PDF document
            query: Query to find relevant provisions (e.g., "Article 5", "inheritance")
            
        Returns:
            List of dictionaries with extracted provisions, including:
            - text: The extracted text
            - page: Page number
            - article: Article number if identified
            - section: Section identifier if available
        """
        results = []
        
        try:
            # Open the document
            doc = fitz.open(document_path)
            
            # Prepare regex patterns for finding articles and sections
            article_pattern = re.compile(r'(Article|المادة)\s+(\d+[a-zA-Z]*)', re.IGNORECASE)
            
            # Process each page
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # Check if the query terms are in the text
                if query.lower() in text.lower():
                    # Find article references
                    matches = article_pattern.finditer(text)
                    
                    for match in matches:
                        article_type = match.group(1)  # "Article" or "المادة"
                        article_num = match.group(2)   # The article number
                        
                        # Find the start position of this article
                        start_pos = match.start()
                        
                        # Find the next article to determine the end of this article
                        next_match = article_pattern.search(text[start_pos + 1:])
                        if next_match:
                            end_pos = start_pos + 1 + next_match.start()
                            article_text = text[start_pos:end_pos].strip()
                        else:
                            # If no next article, take the rest of the page
                            article_text = text[start_pos:].strip()
                        
                        # Add to results
                        results.append({
                            "text": article_text,
                            "page": page_num + 1,  # 1-based page numbering
                            "article": f"{article_type} {article_num}",
                            "document": os.path.basename(document_path)
                        })
            
            # Close the document
            doc.close()
            
        except Exception as e:
            st.error(f"Error extracting provision: {str(e)}")
        
        return results
    
    def find_legal_provisions(self, document_paths: List[str], query: str) -> List[Dict[str, str]]:
        """
        Find legal provisions across multiple documents.
        
        Args:
            document_paths: List of paths to PDF documents
            query: Query to find relevant provisions
            
        Returns:
            List of dictionaries with extracted provisions
        """
        all_results = []
        
        for doc_path in document_paths:
            results = self.extract_provision(doc_path, query)
            all_results.extend(results)
        
        return all_results
    
    def compare_provisions(self, provision1: Dict[str, str], provision2: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
        """
        Compare two legal provisions and highlight differences.
        
        Args:
            provision1: First provision dictionary
            provision2: Second provision dictionary
            
        Returns:
            Tuple containing:
            - similar_lines: Lines that are similar between provisions
            - unique_to_first: Lines unique to the first provision
            - unique_to_second: Lines unique to the second provision
        """
        # Split text into lines
        text1 = provision1["text"].split("\n")
        text2 = provision2["text"].split("\n")
        
        # Use difflib to compare the text
        differ = difflib.Differ()
        diff = list(differ.compare(text1, text2))
        
        # Categorize the differences
        similar_lines = []
        unique_to_first = []
        unique_to_second = []
        
        for line in diff:
            if line.startswith("  "):  # Common line
                similar_lines.append(line[2:])
            elif line.startswith("- "):  # Unique to first text
                unique_to_first.append(line[2:])
            elif line.startswith("+ "):  # Unique to second text
                unique_to_second.append(line[2:])
        
        return similar_lines, unique_to_first, unique_to_second
    
    def generate_html_diff(self, provision1: Dict[str, str], provision2: Dict[str, str]) -> str:
        """
        Generate HTML with highlighted differences between two provisions.
        
        Args:
            provision1: First provision dictionary
            provision2: Second provision dictionary
            
        Returns:
            HTML string with highlighted differences
        """
        # Split text into lines
        text1 = provision1["text"].split("\n")
        text2 = provision2["text"].split("\n")
        
        # Generate HTML diff
        diff = difflib.HtmlDiff()
        html = diff.make_file(text1, text2, 
                             fromdesc=f"{provision1['document']} - {provision1['article']}", 
                             todesc=f"{provision2['document']} - {provision2['article']}")
        
        return html
    
    def get_highlighted_text(self, provision: Dict[str, str], unique_lines: List[str]) -> str:
        """
        Get the highlighted text for a provision with unique lines.
        
        Args:
            provision: Provision dictionary
            unique_lines: List of unique lines
            
        Returns:
            Highlighted text as a string
        """
        text = provision["text"]
        for line in unique_lines:
            text = text.replace(line, f"**{line}**")
        return text
    
    def ai_find_legal_provisions(self, document_paths: List[str], query: str) -> List[Dict[str, str]]:
        """
        Find legal provisions across multiple documents using AI-powered search.
        
        Args:
            document_paths: List of paths to PDF documents
            query: Query to find relevant provisions (handles Arabic text better)
            
        Returns:
            List of dictionaries with extracted provisions
        """
        all_results = []
        
        # Basic results using traditional search
        basic_results = self.find_legal_provisions(document_paths, query)
        
        # If we found results with basic search, use them as a starting point
        if basic_results:
            all_results.extend(basic_results)
        
        # For each document, extract more potential matches using AI
        for doc_path in document_paths:
            try:
                # Open the document and read its metadata
                doc = fitz.open(doc_path)
                doc_name = os.path.basename(doc_path)
                
                # For each page, analyze content with AI if it might contain relevant information
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    
                    # Skip pages that are clearly not relevant
                    if len(text.strip()) < 50:  # Skip nearly empty pages
                        continue
                        
                    # Check if this page might be relevant with a simple heuristic
                    # before using the more expensive AI call
                    keywords = query.lower().split()
                    text_lower = text.lower()
                    
                    # Skip if no keywords match at all
                    if not any(keyword in text_lower for keyword in keywords):
                        continue
                    
                    # Now use AI to extract relevant provisions
                    prompt = f"""
                    You are an expert legal assistant specializing in Omani law. 
                    I'm looking for legal provisions related to: "{query}"
                    
                    Analyze the following page content and determine if it contains relevant legal provisions. 
                    If it does, identify the specific article numbers and section titles.
                    
                    PAGE CONTENT:
                    {text[:1500]}  # Limit to 1500 chars to avoid token limits
                    
                    Is this content relevant to the query? If yes, extract the article numbers and text.
                    Respond in this JSON-like format:
                    RELEVANT: Yes/No
                    ARTICLE: Article number or identifier (if found)
                    SECTION: Section title or identifier (if found)
                    EXTRACT: The exact text of the relevant provision
                    """
                    
                    try:
                        # Use AI to analyze the page content
                        response = self.llm.invoke(prompt).content
                        
                        # Parse the response to extract the information
                        if "RELEVANT: Yes" in response:
                            # Extract article info
                            article_match = re.search(r'ARTICLE: (.+)', response)
                            article = article_match.group(1) if article_match else f"Unnamed Provision {page_num+1}"
                            
                            # Extract section info
                            section_match = re.search(r'SECTION: (.+)', response)
                            section = section_match.group(1) if section_match else ""
                            
                            # Extract text
                            extract_match = re.search(r'EXTRACT: (.+)', response, re.DOTALL)
                            extract = extract_match.group(1).strip() if extract_match else text
                            
                            # Append results only if not duplicated
                            provision = {
                                "source": doc_path,
                                "document": doc_name,
                                "page": page_num,
                                "article": article,
                                "section": section,
                                "text": extract
                            }
                            
                            # Check if this provision is already included
                            if not any(r["text"] == extract for r in all_results):
                                all_results.append(provision)
                                
                    except Exception as e:
                        st.error(f"Error in AI analysis: {str(e)}")
                        continue
                    
            except Exception as e:
                st.error(f"Error processing document {doc_path}: {str(e)}")
        
        return all_results
    
    def ai_compare_provisions(self, provision1: Dict[str, str], provision2: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
        """
        Compare two legal provisions using AI for better understanding and highlighting differences.
        
        Args:
            provision1: First provision dictionary
            provision2: Second provision dictionary
            
        Returns:
            Tuple containing:
            - similar_lines: Lines that are similar between provisions
            - unique_to_first: Lines unique to the first provision
            - unique_to_second: Lines unique to the second provision
        """
        # First use the basic comparison to get initial diff lines
        similar, unique1, unique2 = self.compare_provisions(provision1, provision2)
        
        # Now enhance the comparison with AI understanding
        prompt = f"""
        You are an expert legal analyst specializing in Omani law. 
        Compare these two legal provisions and identify the substantial legal differences between them,
        focusing on legal implications rather than just textual differences.
        
        PROVISION 1 ({provision1.get('article', 'Section')}):
        {provision1['text']}
        
        PROVISION 2 ({provision2.get('article', 'Section')}):
        {provision2['text']}
        
        Please identify semantically meaningful differences and similarities, considering the legal context.
        When highlighting differences, don't just focus on wording but on legal impact and meaning.
        
        Respond in this format:
        SIMILAR: List the semantically similar parts (key legal concepts that are the same).
        UNIQUE_TO_FIRST: List meaningful legal elements unique to the first provision.
        UNIQUE_TO_SECOND: List meaningful legal elements unique to the second provision.
        """
        
        try:
            # Use AI to analyze the legal differences
            response = self.llm.invoke(prompt).content
            
            # Parse the response to extract enhanced differentiators
            similar_section = re.search(r'SIMILAR:\s*(.+?)(?=UNIQUE_TO_FIRST:)', response, re.DOTALL)
            unique1_section = re.search(r'UNIQUE_TO_FIRST:\s*(.+?)(?=UNIQUE_TO_SECOND:)', response, re.DOTALL)
            unique2_section = re.search(r'UNIQUE_TO_SECOND:\s*(.+?)(?=\Z|\n\n)', response, re.DOTALL)
            
            # Extract the text if found
            similar_ai = similar_section.group(1).strip().split('\n') if similar_section else []
            unique1_ai = unique1_section.group(1).strip().split('\n') if unique1_section else []
            unique2_ai = unique2_section.group(1).strip().split('\n') if unique2_section else []
            
            # Merge AI analysis with basic difflib results, prioritizing AI analysis
            # but keeping difflib results for completeness
            enhanced_similar = similar_ai or similar
            enhanced_unique1 = unique1_ai or unique1
            enhanced_unique2 = unique2_ai or unique2
            
            return enhanced_similar, enhanced_unique1, enhanced_unique2
            
        except Exception as e:
            st.warning(f"AI-powered comparison failed, falling back to basic comparison: {str(e)}")
            return similar, unique1, unique2
    
    def generate_legal_difference_analysis(self, provision1: Dict[str, str], provision2: Dict[str, str]) -> str:
        """
        Generate AI-powered legal analysis of differences between two provisions.
        
        Args:
            provision1: First provision dictionary
            provision2: Second provision dictionary
            
        Returns:
            AI-powered legal analysis as a string
        """
        prompt = f"""
        You are an expert legal analyst specializing in Omani law. 
        Provide a thorough legal analysis of the differences between these two provisions, 
        discussing the legal implications and practical effects of the differences.
        
        PROVISION 1 ({provision1.get('article', 'Section')}) from {os.path.basename(provision1['source'])}:
        {provision1['text']}
        
        PROVISION 2 ({provision2.get('article', 'Section')}) from {os.path.basename(provision2['source'])}:
        {provision2['text']}
        
        Your analysis should cover:
        1. The key substantive differences between the provisions
        2. The legal impact of these differences
        3. How these differences might affect legal outcomes in practical scenarios
        4. Whether the provisions are contradictory, complementary, or simply addressing different aspects
        5. Recommendations for legal practitioners dealing with these provisions
        
        Format your response as a formal legal analysis with clear headings and structure.
        """
        
        try:
            # Generate the legal analysis
            analysis = self.llm.invoke(prompt).content
            return analysis
        except Exception as e:
            return f"Error generating legal analysis: {str(e)}"
    
    def render_comparison_interface(self, document_paths: List[str]):
        """
        Render the Streamlit interface for legal provision comparison.
        
        Args:
            document_paths: List of paths to PDF documents
        """
        st.subheader("Legal Provision Comparison")
        
        # Input for searching legal provisions
        query = st.text_input("Enter keywords to find legal provisions (e.g., 'inheritance', 'Article 5')")
        
        # Add AI-assisted search option
        use_ai_search = st.checkbox("Use AI for finding provisions", value=True,
                                  help="Enable to use AI for better matching, especially for Arabic text")
                                  
        # Add AI-assisted comparison option
        use_ai_comparison = st.checkbox("Use AI for comparison analysis", value=True,
                                     help="Enable to get AI-powered legal analysis of differences")
        
        if query:
            # Find legal provisions
            if use_ai_search:
                provisions = self.ai_find_legal_provisions(document_paths, query)
            else:
                provisions = self.find_legal_provisions(document_paths, query)
            
            if provisions:
                st.write(f"Found {len(provisions)} provisions matching '{query}'.")
                
                # Allow the user to select provisions to compare
                if len(provisions) >= 2:
                    # Create checkboxes for each provision
                    selected_provisions = []
                    
                    for i, provision in enumerate(provisions):
                        doc_name = os.path.basename(provision["source"])
                        label = f"{doc_name} - {provision.get('article', 'Section')} (Page {provision['page']+1})"
                        
                        if st.checkbox(label, key=f"provision_{i}"):
                            selected_provisions.append(provision)
                    
                    # Compare selected provisions
                    if len(selected_provisions) == 2:
                        st.write("### Comparison Results")
                        
                        # Display the comparison
                        prov1 = selected_provisions[0]
                        prov2 = selected_provisions[1]
                        
                        # Choose comparison method based on user preference
                        if use_ai_comparison:
                            similar, unique1, unique2 = self.ai_compare_provisions(prov1, prov2)
                        else:
                            similar, unique1, unique2 = self.compare_provisions(prov1, prov2)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            doc_name1 = os.path.basename(prov1["source"])
                            st.write(f"**{doc_name1} - {prov1.get('article', 'Section')}**")
                            st.markdown(self.get_highlighted_text(prov1, unique1), unsafe_allow_html=True)
                        
                        with col2:
                            doc_name2 = os.path.basename(prov2["source"])
                            st.write(f"**{doc_name2} - {prov2.get('article', 'Section')}**")
                            st.markdown(self.get_highlighted_text(prov2, unique2), unsafe_allow_html=True)
                        
                        # Generate and display HTML diff
                        html_diff = self.generate_html_diff(provision1, provision2)
                        
                        # Create a download button for the HTML diff
                        st.download_button(
                            label="Download Detailed Comparison",
                            data=html_diff,
                            file_name="legal_comparison.html",
                            mime="text/html"
                        )
                        
                        # Show summary of differences
                        st.subheader("Summary of Differences")
                        
                        if unique1:
                            st.write(f"**Unique to {provision1['document']} - {provision1['article']}:**")
                            for line in unique1:
                                st.write(f"- {line}")
                        
                        if unique2:
                            st.write(f"**Unique to {provision2['document']} - {provision2['article']}:**")
                            for line in unique2:
                                st.write(f"- {line}")
                        
                        if not unique1 and not unique2:
                            st.success("No significant differences found between these provisions.")
                    else:
                        st.warning("Please select different provisions for comparison.")
            else:
                st.warning(f"No provisions found matching '{query}'. Try different keywords.")
        else:
            st.info("Enter keywords to search for legal provisions in the documents.")
