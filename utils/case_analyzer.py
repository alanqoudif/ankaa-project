"""
Case Analysis module for ShariaAI - Structured legal reasoning and analysis.
Level 4 Feature: Case analysis with step-by-step reasoning.
"""
import os
import streamlit as st
import tempfile
from langchain_openai import ChatOpenAI
from utils.env_loader import load_env_vars
from utils.pdf_generator import generate_pdf

class CaseAnalyzer:
    """Analyze legal cases and provide structured reasoning and analysis."""
    
    def __init__(self):
        """Initialize the case analyzer with LLM connection."""
        env_vars = load_env_vars()
        self.openrouter_api_key = env_vars['openrouter_api_key']
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            openai_api_key=self.openrouter_api_key,
            model="qwen/qwen3-235b-a22b:free",
            temperature=0.1,
            max_tokens=3000,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/alanqoudif/ankaa-project",
                "X-Title": "ShariaAI - Omani Legal Assistant"
            }
        )
    
    def analyze_case(self, case_facts, legal_questions=None):
        """
        Analyze a legal case based on the provided facts and questions.
        
        Args:
            case_facts: Description of the case facts
            legal_questions: Specific legal questions to analyze
            
        Returns:
            Dictionary containing structured analysis
        """
        if not legal_questions:
            legal_questions = ["What are the relevant legal principles?", 
                               "How do these principles apply to the facts?",
                               "What is the likely outcome?"]
        
        # Create the prompt for the LLM
        prompt = f"""
        You are a legal expert specializing in Omani law. Analyze the following case using a structured, step-by-step approach:
        
        CASE FACTS:
        {case_facts}
        
        Provide a comprehensive legal analysis addressing the following:
        
        1. ISSUE IDENTIFICATION:
           - Identify the key legal issues presented
           - Specify the areas of law involved
        
        2. APPLICABLE LAW:
           - Identify relevant Omani statutes, regulations, and legal principles
           - Cite specific articles and provisions when possible
        
        3. CASE ANALYSIS:
           - Apply the law to the facts in a step-by-step manner
           - Consider potential counterarguments
           - Evaluate the strength of different legal positions
        
        4. CONCLUSION:
           - Provide a reasoned conclusion for each issue
           - Offer a final assessment of the case
        
        5. RECOMMENDATIONS:
           - Suggest next steps or actions
           - Address risk mitigation strategies if applicable
        
        SPECIFIC LEGAL QUESTIONS TO ADDRESS:
        {', '.join(legal_questions)}
        
        Format your analysis in a clear, structured manner with appropriate headings and subheadings.
        """
        
        try:
            # Get analysis from LLM
            response = self.llm.invoke(prompt)
            analysis = response.content
            
            # Parse the analysis into structured sections
            sections = self._parse_analysis(analysis)
            
            return {
                "case_facts": case_facts,
                "legal_questions": legal_questions,
                "analysis": analysis,
                "structured_sections": sections
            }
            
        except Exception as e:
            st.error(f"Error analyzing case: {str(e)}")
            return None
    
    def _parse_analysis(self, analysis):
        """
        Parse the analysis text into structured sections.
        
        Args:
            analysis: The raw analysis text from the LLM
            
        Returns:
            Dictionary containing structured sections
        """
        sections = {
            "issue_identification": "",
            "applicable_law": "",
            "case_analysis": "",
            "conclusion": "",
            "recommendations": ""
        }
        
        # Simple parsing based on headings
        current_section = None
        
        for line in analysis.split('\n'):
            line = line.strip()
            
            if "ISSUE IDENTIFICATION" in line.upper() or "1." in line and "ISSUE" in line.upper():
                current_section = "issue_identification"
                sections[current_section] += line + "\n"
            elif "APPLICABLE LAW" in line.upper() or "2." in line and "LAW" in line.upper():
                current_section = "applicable_law"
                sections[current_section] += line + "\n"
            elif "CASE ANALYSIS" in line.upper() or "3." in line and "ANALYSIS" in line.upper():
                current_section = "case_analysis"
                sections[current_section] += line + "\n"
            elif "CONCLUSION" in line.upper() or "4." in line and "CONCLUSION" in line.upper():
                current_section = "conclusion"
                sections[current_section] += line + "\n"
            elif "RECOMMENDATIONS" in line.upper() or "5." in line and "RECOMMENDATIONS" in line.upper():
                current_section = "recommendations"
                sections[current_section] += line + "\n"
            elif current_section:
                sections[current_section] += line + "\n"
        
        return sections
    
    def generate_case_report(self, analysis_result, client_name=None, case_reference=None):
        """
        Generate a PDF report from the case analysis.
        
        Args:
            analysis_result: The result from analyze_case
            client_name: Name of the client (optional)
            case_reference: Reference number or identifier for the case (optional)
            
        Returns:
            Path to the generated PDF file
        """
        if not analysis_result:
            return None
        
        # Create a title for the report
        title = "Legal Case Analysis"
        if case_reference:
            title += f" - {case_reference}"
        
        # Format the sections for the report
        sections = []
        
        # Add case facts
        sections.append({
            "heading": "Case Facts",
            "content": analysis_result["case_facts"]
        })
        
        # Add legal questions
        sections.append({
            "heading": "Legal Questions",
            "content": "\n".join([f"- {q}" for q in analysis_result["legal_questions"]])
        })
        
        # Add structured analysis sections
        for key, content in analysis_result["structured_sections"].items():
            if content.strip():
                heading = key.replace("_", " ").title()
                sections.append({
                    "heading": heading,
                    "content": content
                })
        
        # Generate the PDF
        from utils.pdf_generator import create_custom_report
        pdf_path = create_custom_report(title, sections, client_name=client_name)
        
        return pdf_path
    
    def render_case_analysis_interface(self):
        """Render the case analysis interface in Streamlit."""
        st.subheader("Legal Case Analysis")
        st.write("Enter case facts and questions for a detailed legal analysis")
        
        # Case inputs
        st.write("#### Case Information")
        client_name = st.text_input("Client Name (Optional)")
        case_reference = st.text_input("Case Reference (Optional)")
        
        case_facts = st.text_area("Case Facts", height=200, 
                                 placeholder="Describe the facts of the case in detail...")
        
        # Legal questions
        st.write("#### Legal Questions")
        st.write("Enter specific legal questions to be addressed in the analysis:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            question1 = st.text_input("Question 1", "What are the relevant legal principles?")
            question2 = st.text_input("Question 2", "How do these principles apply to the facts?")
            question3 = st.text_input("Question 3", "What is the likely outcome?")
        
        with col2:
            question4 = st.text_input("Question 4 (Optional)")
            question5 = st.text_input("Question 5 (Optional)")
        
        # Collect all non-empty questions
        legal_questions = [q for q in [question1, question2, question3, question4, question5] if q]
        
        # Analysis button
        if st.button("Analyze Case"):
            if case_facts:
                with st.spinner("Analyzing the case... This may take a moment."):
                    # Perform the analysis
                    analysis_result = self.analyze_case(case_facts, legal_questions)
                    
                    if analysis_result:
                        # Display the analysis
                        st.success("Analysis complete!")
                        
                        st.markdown("### Analysis Results")
                        
                        # Display each section with expanders
                        for key, content in analysis_result["structured_sections"].items():
                            if content.strip():
                                with st.expander(key.replace("_", " ").title()):
                                    st.markdown(content)
                        
                        # Generate PDF report
                        try:
                            pdf_path = self.generate_case_report(
                                analysis_result, 
                                client_name=client_name, 
                                case_reference=case_reference
                            )
                            
                            if pdf_path:
                                with open(pdf_path, "rb") as f:
                                    pdf_bytes = f.read()
                                
                                st.download_button(
                                    label="Download Analysis Report",
                                    data=pdf_bytes,
                                    file_name=f"case_analysis_{case_reference or 'report'}.pdf",
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating PDF report: {str(e)}")
            else:
                st.warning("Please enter case facts to perform analysis.")
