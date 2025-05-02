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

class LegalComparison:
    """Handle comparison between legal provisions with difference highlighting."""
    
    def __init__(self):
        """Initialize the legal comparison module."""
        pass
    
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
    
    def render_comparison_interface(self, document_paths: List[str]):
        """
        Render the comparison interface in Streamlit.
        
        Args:
            document_paths: List of paths to PDF documents
        """
        st.subheader("Legal Provision Comparison")
        
        # Search box for provisions
        query = st.text_input("Enter keywords to find legal provisions (e.g., 'inheritance', 'Article 5')")
        
        if query:
            with st.spinner("Searching for relevant provisions..."):
                provisions = self.find_legal_provisions(document_paths, query)
            
            if provisions:
                st.success(f"Found {len(provisions)} relevant provisions")
                
                # Display found provisions
                for i, provision in enumerate(provisions):
                    with st.expander(f"{provision['document']} - {provision['article']} (Page {provision['page']})"):
                        st.write(provision["text"])
                
                # Select provisions for comparison
                st.subheader("Compare Provisions")
                
                # Create two columns for selection
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("First Provision")
                    provision1_index = st.selectbox("Select first provision", 
                                                   range(len(provisions)), 
                                                   format_func=lambda i: f"{provisions[i]['document']} - {provisions[i]['article']}")
                
                with col2:
                    st.write("Second Provision")
                    provision2_index = st.selectbox("Select second provision", 
                                                   range(len(provisions)), 
                                                   format_func=lambda i: f"{provisions[i]['document']} - {provisions[i]['article']}")
                
                # Compare button
                if st.button("Compare Selected Provisions"):
                    if provision1_index != provision2_index:
                        provision1 = provisions[provision1_index]
                        provision2 = provisions[provision2_index]
                        
                        # Get differences
                        similar, unique1, unique2 = self.compare_provisions(provision1, provision2)
                        
                        # Display comparison
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"### {provision1['document']} - {provision1['article']}")
                            # Highlight unique sections
                            text = provision1["text"]
                            for line in unique1:
                                text = text.replace(line, f"**{line}**")
                            st.markdown(text)
                        
                        with col2:
                            st.write(f"### {provision2['document']} - {provision2['article']}")
                            # Highlight unique sections
                            text = provision2["text"]
                            for line in unique2:
                                text = text.replace(line, f"**{line}**")
                            st.markdown(text)
                        
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
