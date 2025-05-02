"""
Section Navigator for ShariaAI Omani Legal Assistant.
This module enables hierarchical browsing and navigation of legal documents.
"""
import re
import fitz  # PyMuPDF
import streamlit as st
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
    """Navigator for hierarchical browsing of legal documents."""
    
    def __init__(self):
        self.documents = {}  # Map of doc_name to root section
        self.current_doc = None
        self.current_section = None
    
    def load_document(self, file_path: str) -> bool:
        """
        Load a document and extract its hierarchical structure.
        Returns True if successful, False otherwise.
        """
        try:
            doc_name = file_path.split("/")[-1]
            doc = fitz.open(file_path)
            
            # Create root section for the document
            root = LegalSection(doc_name, "", 0)
            root.source_doc = doc_name
            
            # Extract text and identify sections
            section_pattern = re.compile(r'^(Article|Section|Chapter)\s+(\d+[a-zA-Z]*)[:.\s]*(.*?)$', re.MULTILINE)
            subsection_pattern = re.compile(r'^(\d+)[\.\s]+(.*?)$', re.MULTILINE)
            
            current_section = None
            current_subsection = None
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # Find all section matches
                section_matches = section_pattern.finditer(text)
                for match in section_matches:
                    section_type = match.group(1)
                    section_num = match.group(2)
                    section_title = match.group(3).strip()
                    
                    # Create new section
                    title = f"{section_type} {section_num}: {section_title}"
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
                    subsection_matches = subsection_pattern.finditer(text)
                    for match in subsection_matches:
                        subsection_num = match.group(1)
                        subsection_content = match.group(2).strip()
                        
                        # Create new subsection
                        title = f"{subsection_num}. {subsection_content[:50]}..."
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
            
            # Store the document
            self.documents[doc_name] = root
            
            # Clean up
            doc.close()
            
            return True
        
        except Exception as e:
            st.error(f"Error loading document for section navigation: {str(e)}")
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
    
    def get_section_summary(self, section: LegalSection, detail_level: int = 1) -> str:
        """
        Generate a summary of the section with adjustable detail level.
        
        detail_level:
            1 = Brief summary (title + first paragraph)
            2 = Medium summary (title + first few paragraphs)
            3 = Full content
        """
        if not section:
            return "No section selected."
        
        if detail_level == 1:
            # Brief summary
            paragraphs = section.content.split("\n\n")
            if paragraphs:
                return f"{section.title}\n\n{paragraphs[0]}"
            return section.title
        
        elif detail_level == 2:
            # Medium summary
            paragraphs = section.content.split("\n\n")
            if len(paragraphs) > 3:
                content = "\n\n".join(paragraphs[:3])
                return f"{section.title}\n\n{content}\n\n..."
            return f"{section.title}\n\n{section.content}"
        
        else:
            # Full content
            return f"{section.title}\n\n{section.content}"
    
    def find_cross_references(self, section: LegalSection) -> List[Tuple[str, LegalSection]]:
        """
        Find cross-references in a section to other sections.
        Returns a list of (reference text, referenced section) tuples.
        """
        if not section or not section.content:
            return []
        
        references = []
        
        # Pattern to match references like "Article X", "Section Y", etc.
        ref_pattern = re.compile(r'(Article|Section|Chapter)\s+(\d+[a-zA-Z]*)', re.IGNORECASE)
        
        # Find all references in the content
        matches = ref_pattern.finditer(section.content)
        for match in matches:
            ref_type = match.group(1)
            ref_num = match.group(2)
            ref_text = f"{ref_type} {ref_num}"
            
            # Search for the referenced section
            for doc_name, root in self.documents.items():
                for child in root.children:
                    if child.title.startswith(ref_text):
                        references.append((ref_text, child))
                        break
        
        return references
    
    def render_section_navigator(self):
        """Render the section navigator UI in Streamlit."""
        st.subheader("Section Navigator")
        
        # Document selector
        doc_names = self.get_documents()
        if not doc_names:
            st.warning("No documents loaded for navigation. Please load documents first.")
            return
        
        selected_doc = st.selectbox("Select Document", doc_names)
        
        if selected_doc:
            root = self.select_document(selected_doc)
            if not root:
                st.error(f"Error loading document: {selected_doc}")
                return
            
            # Section selector
            sections = self.get_sections(selected_doc)
            if not sections:
                st.warning(f"No sections found in {selected_doc}")
                return
            
            section_titles = [section.title for section in sections]
            selected_section_title = st.selectbox("Select Section", section_titles)
            
            if selected_section_title:
                # Find the selected section
                selected_section = next((s for s in sections if s.title == selected_section_title), None)
                
                if selected_section:
                    # Detail level slider
                    detail_level = st.slider("Detail Level", min_value=1, max_value=3, value=2, 
                                             help="1 = Brief, 2 = Medium, 3 = Full")
                    
                    # Display the section summary
                    summary = self.get_section_summary(selected_section, detail_level)
                    st.markdown(f"### {selected_section.title}")
                    st.markdown(summary)
                    
                    # Display subsections if any
                    if selected_section.children:
                        st.markdown("### Subsections")
                        for subsection in selected_section.children:
                            with st.expander(subsection.title):
                                st.markdown(self.get_section_summary(subsection, detail_level))
                    
                    # Display cross-references if any
                    cross_refs = self.find_cross_references(selected_section)
                    if cross_refs:
                        st.markdown("### Cross References")
                        for ref_text, ref_section in cross_refs:
                            st.markdown(f"- [{ref_text}]({ref_section.get_full_path()}): {ref_section.title}")
                    
                    # Source information
                    st.markdown(f"**Source**: {selected_section.source_doc}, Page {selected_section.page_num + 1}")
