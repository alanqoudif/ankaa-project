"""
Section Navigator for ShariaAI Omani Legal Assistant.
This module enables hierarchical browsing and navigation of legal documents with Arabic support.
"""
import re
import fitz  # PyMuPDF
import streamlit as st
import logging
from typing import Dict, List, Tuple, Optional

class LegalSection:
    """Represents a section of a legal document with hierarchical structure."""
    def __init__(self, title: str, content: str, level: int, parent=None):
        self.title = title
        self.content = content
        self.level = level
        self.parent = parent
        self.children = []
        self.source_doc = ""
        self.page_num = 0
    
    def add_child(self, child):
        """Add a child section to this section."""
        child.parent = self
        self.children.append(child)
    
    def get_full_path(self):
        """Get the full path of this section."""
        if self.parent is None:
            return self.title
        return f"{self.parent.get_full_path()} > {self.title}"
    
    def __str__(self):
        return f"{self.title} (Level {self.level}, {len(self.children)} children)"

class SectionNavigator:
    """Navigator for hierarchical browsing of legal documents with Arabic support."""
    
    def __init__(self):
        self.documents = {}  # Map of doc_name to root section
        self.current_doc = None
        self.current_section = None
    
    def load_document(self, file_path: str) -> bool:
        """
        Load a document and extract its hierarchical structure with Arabic support.
        Returns True if successful, False otherwise.
        """
        try:
            doc_name = file_path.split("/")[-1]
            doc = fitz.open(file_path)
            
            # Create root section for the document
            root = LegalSection(doc_name, "", 0)
            root.source_doc = doc_name
            
            # Extract text and identify sections
            # Updated patterns to support both English and Arabic legal document structures
            section_patterns = [
                # Traditional English patterns
                re.compile(r'^(Article|Section|Chapter)\s+(\d+[a-zA-Z]*)[:.\s]*(.*?)$', re.MULTILINE | re.IGNORECASE),
                
                # Arabic patterns for sections (المادة = Article, الفصل = Chapter, etc.)
                re.compile(r'^(المادة|الفصل|القسم|مادة|فصل)\s*(\d+[٠-٩]*)[:.\s-]*(.*?)$', re.MULTILINE),
                
                # Simple numbered article pattern (common in Arabic legal docs)
                re.compile(r'^(\(\s*\d+\s*\)|\d+\s*[\.-])\s*(.*?)$', re.MULTILINE)
            ]
            
            # Subsection patterns
            subsection_patterns = [
                # Traditional numbered subsections (1., 2., etc.)
                re.compile(r'^(\d+[a-zA-Z٠-٩]*)[\.\s-]+(.*?)$', re.MULTILINE),
                
                # Arabic numbered subsections
                re.compile(r'^(\(\s*[أ-ي١٢٣٤٥٦٧٨٩٠]\s*\))\s*(.*?)$', re.MULTILINE),
                
                # Lettered subsections ((أ), (ب), etc.)
                re.compile(r'^(\(\s*[أ-ي]\s*\))\s*(.*?)$', re.MULTILINE)
            ]
            
            current_section = None
            current_subsection = None
            sections_found = False
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # First pass: Try to find major sections
                for pattern in section_patterns:
                    section_matches = pattern.finditer(text)
                    for match in section_matches:
                        sections_found = True
                        if len(match.groups()) >= 2:
                            # For patterns with type, number, and title
                            if len(match.groups()) >= 3:
                                section_type = match.group(1)
                                section_num = match.group(2)
                                section_title = match.group(3).strip() if match.group(3) else ""
                                
                                # Create title based on matched groups
                                if section_title:
                                    title = f"{section_type} {section_num}: {section_title}"
                                else:
                                    title = f"{section_type} {section_num}"
                            else:
                                # For simpler patterns with just a marker and content
                                section_marker = match.group(1)
                                section_content = match.group(2).strip() if len(match.groups()) > 1 else ""
                                title = f"{section_marker} {section_content[:50]}..."
                            
                            # Create new section
                            new_section = LegalSection(title, "", 1, root)
                            new_section.source_doc = doc_name
                            new_section.page_num = page_num
                            
                            # Add to root
                            root.add_child(new_section)
                            
                            # Update current section
                            current_section = new_section
                            current_subsection = None
                
                # Find all subsection matches if we have a current section
                if current_section:
                    for pattern in subsection_patterns:
                        subsection_matches = pattern.finditer(text)
                        for match in subsection_matches:
                            if len(match.groups()) >= 2:
                                subsection_num = match.group(1)
                                subsection_content = match.group(2).strip()
                                
                                # Create new subsection - limit title length for display
                                max_title_length = 50
                                truncated_content = subsection_content[:max_title_length] + ("..." if len(subsection_content) > max_title_length else "")
                                title = f"{subsection_num} {truncated_content}"
                                new_subsection = LegalSection(title, subsection_content, 2, current_section)
                                new_subsection.source_doc = doc_name
                                new_subsection.page_num = page_num
                                
                                # Add to current section
                                current_section.add_child(new_subsection)
                                
                                # Update current subsection
                                current_subsection = new_subsection
                
                # If we couldn't find any sections or subsections, add the page content
                # to the current section or subsection
                if current_subsection:
                    current_subsection.content += f"\n{text}"
                elif current_section:
                    current_section.content += f"\n{text}"
                else:
                    # If no sections found, add the content to the root
                    root.content += f"\n{text}"
            
            # If no sections were found, try a more aggressive approach to find structure
            if not sections_found:
                st.warning(f"No standard sections found in document: {doc_name}. Trying alternate section detection...")
                
                # Reprocess with more general patterns
                fallback_patterns = [
                    # Match any line that starts with a number followed by a period
                    re.compile(r'^(\d+)[\.:\s-](.*?)$', re.MULTILINE),
                    
                    # Match any capitalized line or line with bold formatting (possible section heading)
                    re.compile(r'^([A-Z][A-Z\s]+|[أ-ي][أ-ي\s]+)[:\.\s-]*(.*?)$', re.MULTILINE)
                ]
                
                # Process each page with fallback patterns
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    page_sections_found = False
                    
                    for pattern in fallback_patterns:
                        matches = pattern.finditer(text)
                        for match in matches:
                            page_sections_found = True
                            if len(match.groups()) >= 1:
                                marker = match.group(1)
                                title_text = match.group(2).strip() if len(match.groups()) > 1 else ""
                                
                                # Create a section with whatever we found
                                title = f"{marker}: {title_text[:50]}..." if title_text else f"{marker}"
                                new_section = LegalSection(title, "", 1, root)
                                new_section.source_doc = doc_name
                                new_section.page_num = page_num
                                
                                # Add to root
                                root.add_child(new_section)
                    
                    # If still no sections, create a page-based section
                    if not page_sections_found and not sections_found:
                        # Create a section for this page
                        page_title = f"Page {page_num+1}"
                        page_section = LegalSection(page_title, text, 1, root)
                        page_section.source_doc = doc_name
                        page_section.page_num = page_num
                        
                        # Add to root
                        root.add_child(page_section)
                        sections_found = True
            
            # Store the document
            self.documents[doc_name] = root
            
            # Clean up
            doc.close()
            
            # Report success or partial success
            if sections_found:
                st.success(f"Loaded document: {doc_name} with {len(root.children)} sections")
                return True
            else:
                st.warning(f"Document loaded but no sections identified: {doc_name}")
                return True  # Still return True as we did create a basic structure
        
        except Exception as e:
            st.error(f"Error loading document for section navigation: {str(e)}")
            logging.error(f"Section navigator error: {str(e)}", exc_info=True)
            return False
    
    def load_documents(self, file_paths: List[str]) -> int:
        """
        Load multiple documents and extract their hierarchical structure.
        Returns the number of successfully loaded documents.
        """
        success_count = 0
        for file_path in file_paths:
            if self.load_document(file_path):
                success_count += 1
        return success_count
    
    def get_documents(self) -> List[str]:
        """Get a list of document names."""
        return list(self.documents.keys())
    
    def select_document(self, doc_name: str) -> Optional[LegalSection]:
        """Select a document by name and return its root section."""
        if doc_name in self.documents:
            self.current_doc = doc_name
            self.current_section = self.documents[doc_name]
            return self.current_section
        return None
    
    def get_sections(self, doc_name: str) -> List[LegalSection]:
        """Get all top-level sections in a document."""
        if doc_name in self.documents:
            return self.documents[doc_name].children
        return []
    
    def select_section(self, section_path: str) -> Optional[LegalSection]:
        """
        Select a section by its path string (e.g., "Root > Chapter 1 > Article 5").
        Returns the selected section if found, None otherwise.
        """
        if not self.current_doc:
            return None
        
        parts = section_path.split(" > ")
        if len(parts) < 2:  # Just the root
            return self.documents[self.current_doc]
        
        # Start from the root
        section = self.documents[self.current_doc]
        
        # Navigate down the path
        for i in range(1, len(parts)):
            found = False
            for child in section.children:
                if child.title == parts[i]:
                    section = child
                    found = True
                    break
            
            if not found:
                return None
        
        self.current_section = section
        return section
    
    def render_section_navigator(self):
        """Render the section navigator interface in Streamlit."""
        # Select document
        st.subheader("Document Selection")
        
        # Get document list and ensure it's not empty
        documents = self.get_documents()
        if not documents:
            st.warning("No documents loaded. Please ensure documents are loaded first.")
            return
        
        # Document selector
        selected_doc = st.selectbox("Select a document", documents)
        
        if selected_doc:
            # Get sections
            sections = self.get_sections(selected_doc)
            
            if sections:
                # Format section titles for display
                section_titles = [section.title for section in sections]
                
                # Section selector
                st.subheader("Section Navigation")
                selected_section_title = st.selectbox("Select a section", section_titles)
                
                if selected_section_title:
                    # Find the selected section
                    selected_section = next((s for s in sections if s.title == selected_section_title), None)
                    
                    if selected_section:
                        # Display section content
                        st.subheader("Section Content")
                        
                        # Add metadata
                        st.info(f"Document: {selected_doc} | Page: {selected_section.page_num + 1}")
                        
                        # Show section content
                        st.markdown(f"### {selected_section.title}")
                        
                        # Clean and display the content
                        content = selected_section.content.strip()
                        if content:
                            st.markdown(content)
                        else:
                            st.write("No content available for this section.")
                        
                        # If the section has subsections, show them
                        if selected_section.children:
                            st.subheader("Subsections")
                            for subsection in selected_section.children:
                                with st.expander(subsection.title):
                                    st.markdown(subsection.content)
            else:
                st.warning(f"No sections found in document: {selected_doc}")
                
                # Offer troubleshooting option
                if st.button("Try alternate section detection"):
                    # Remove the current document from the map
                    if selected_doc in self.documents:
                        del self.documents[selected_doc]
                    
                    # Get the file path from original loading
                    doc_path = None
                    # This logic depends on how you originally loaded the documents
                    # You may need to keep track of original file paths
                    
                    if doc_path:
                        # Try loading with more aggressive patterns
                        success = self.load_document(doc_path)
                        if success:
                            st.success("Document reloaded with alternate detection")
                            st.rerun()
                    else:
                        st.error("Unable to find original document path for reloading")
