"""
Document Drafter module for ShariaAI - Automated drafting of legal documents.
Level 4 Feature: Automated drafting of legal letters/memos with official formatting.
"""
import os
import streamlit as st
import tempfile
from datetime import datetime
from langchain_openai import ChatOpenAI
from utils.env_loader import load_env_vars
from utils.pdf_generator import generate_pdf, create_custom_report

class DocumentDrafter:
    """Generate legal documents, letters, and memos with official formatting."""
    
    def __init__(self):
        """Initialize the document drafter with LLM connection."""
        env_vars = load_env_vars()
        self.openrouter_api_key = env_vars['openrouter_api_key']
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            openai_api_key=self.openrouter_api_key,
            model="qwen/qwen3-235b-a22b:free",
            temperature=0.2,
            max_tokens=2500,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/alanqoudif/ankaa-project",
                "X-Title": "ShariaAI - Omani Legal Assistant"
            }
        )
        
        # Templates for different document types
        self.templates = {
            "legal_memo": self._legal_memo_template,
            "legal_opinion": self._legal_opinion_template,
            "demand_letter": self._demand_letter_template,
            "contract_agreement": self._contract_agreement_template
        }
    
    def _legal_memo_template(self, params):
        """Template for generating a legal memo."""
        prompt = f"""
        Write a professional legal memorandum based on the following parameters:
        
        TO: {params.get('recipient', '[Recipient]')}
        FROM: {params.get('sender', '[Sender]')}
        DATE: {params.get('date', datetime.now().strftime('%B %d, %Y'))}
        SUBJECT: {params.get('subject', 'Legal Analysis')}
        
        ISSUE:
        {params.get('issue', 'What legal issues must be addressed?')}
        
        BRIEF ANSWER:
        [Generate a concise summary of your conclusion]
        
        FACTS:
        {params.get('facts', 'Relevant factual background of the case.')}
        
        ANALYSIS:
        [Provide a detailed legal analysis that discusses relevant Omani laws, regulations, and precedents. Include specific citations to legal authorities where appropriate. Analyze the strengths and weaknesses of the legal position.]
        
        CONCLUSION:
        [Summarize your findings and provide clear recommendations for next steps.]
        
        Please draft a complete and professional legal memorandum following this structure. Use formal language appropriate for internal legal communication. Cite relevant Omani legal authorities where applicable.
        """
        
        return self._generate_content(prompt)
    
    def _legal_opinion_template(self, params):
        """Template for generating a legal opinion letter."""
        prompt = f"""
        Write a formal legal opinion letter based on the following parameters:
        
        LETTERHEAD: {params.get('firm_name', 'Legal Office')}
        DATE: {params.get('date', datetime.now().strftime('%B %d, %Y'))}
        
        ADDRESSEE:
        {params.get('addressee', '[Client Name and Address]')}
        
        RE: {params.get('subject', 'Legal Opinion on [Matter]')}
        
        Dear {params.get('salutation', 'Sir/Madam')},
        
        INTRODUCTION:
        [Introduce the purpose of this opinion letter and confirm your engagement to provide a legal opinion on the stated matter.]
        
        FACTS AND BACKGROUND:
        {params.get('facts', 'Relevant factual background of the matter.')}
        
        LEGAL QUESTIONS PRESENTED:
        {params.get('questions', 'What specific legal questions need to be addressed?')}
        
        LEGAL ANALYSIS:
        [Provide a comprehensive legal analysis that addresses each question presented. Reference specific provisions of Omani law. Explain your reasoning clearly.]
        
        OPINION:
        [State your legal opinion on each question, derived from your analysis. Be clear and unambiguous.]
        
        QUALIFICATIONS AND LIMITATIONS:
        [State any qualifications or limitations to your opinion, e.g., assumptions made, documents reviewed, scope limitations.]
        
        CONCLUSION:
        [Summarize your opinion and offer closing remarks.]
        
        Sincerely,
        
        {params.get('signature', '[Attorney Name]')}
        {params.get('title', '[Title]')}
        {params.get('firm_name', '[Firm Name]')}
        
        Please draft a complete and professional legal opinion letter following this structure. Use formal language appropriate for client communication. Cite relevant Omani legal authorities where applicable.
        """
        
        return self._generate_content(prompt)
    
    def _demand_letter_template(self, params):
        """Template for generating a demand letter."""
        prompt = f"""
        Write a formal demand letter based on the following parameters:
        
        LETTERHEAD: {params.get('firm_name', 'Legal Office')}
        DATE: {params.get('date', datetime.now().strftime('%B %d, %Y'))}
        
        ADDRESSEE:
        {params.get('addressee', '[Recipient Name and Address]')}
        
        RE: {params.get('subject', 'Demand for [Nature of Demand]')}
        
        Dear {params.get('salutation', 'Sir/Madam')},
        
        INTRODUCTION:
        [Introduce yourself and state that you represent the client. Briefly state the purpose of the letter.]
        
        FACTUAL BACKGROUND:
        {params.get('facts', 'Relevant factual background leading to this demand.')}
        
        LEGAL BASIS:
        [Explain the legal basis for the demand. Cite relevant provisions of Omani law that support your client's position.]
        
        DEMAND:
        {params.get('demand', 'Clearly state what action is being demanded.')}
        
        DEADLINE AND CONSEQUENCES:
        [Specify the deadline for compliance. State the legal consequences that may follow if the recipient fails to comply with the demand.]
        
        CLOSING:
        [Include standard closing language, reserving all legal rights and remedies. Invite contact to discuss resolution.]
        
        Sincerely,
        
        {params.get('signature', '[Attorney Name]')}
        {params.get('title', '[Title]')}
        {params.get('firm_name', '[Firm Name]')}
        
        Please draft a complete and professional demand letter following this structure. Use formal, authoritative language. The tone should be firm but professional. Cite relevant Omani legal authorities where applicable.
        """
        
        return self._generate_content(prompt)
    
    def _contract_agreement_template(self, params):
        """Template for generating a contract or agreement."""
        prompt = f"""
        Write a formal contract agreement based on the following parameters:
        
        TITLE: {params.get('title', 'AGREEMENT')}
        
        PARTIES:
        {params.get('parties', '1. [First Party Name and Details]\n2. [Second Party Name and Details]')}
        
        DATE: {params.get('date', datetime.now().strftime('%B %d, %Y'))}
        
        RECITALS:
        [Background information explaining why the parties are entering into this agreement]
        
        NOW THEREFORE, in consideration of the mutual covenants contained herein, the parties agree as follows:
        
        AGREEMENT TERMS:
        {params.get('terms', 'Outline the key terms of the agreement.')}
        
        SCOPE:
        {params.get('scope', 'Define the scope of the agreement.')}
        
        TERM AND TERMINATION:
        [Specify the duration of the agreement and conditions for termination]
        
        COMPENSATION:
        {params.get('compensation', 'Detail any payment or compensation structure.')}
        
        REPRESENTATIONS AND WARRANTIES:
        [Standard representations and warranties appropriate for this type of agreement under Omani law]
        
        GOVERNING LAW:
        [Specify that the agreement is governed by the laws of Oman]
        
        DISPUTE RESOLUTION:
        [Specify how disputes will be resolved, e.g., courts of Oman, arbitration]
        
        MISCELLANEOUS PROVISIONS:
        [Include standard miscellaneous provisions appropriate under Omani law]
        
        SIGNATURES:
        
        ________________________            ________________________
        {params.get('party1_name', 'First Party')}                      {params.get('party2_name', 'Second Party')}
        
        Date: ___________________            Date: ___________________
        
        Please draft a complete and professional contract agreement following this structure. Use formal legal language appropriate for binding agreements. Ensure the agreement complies with Omani legal requirements for contracts.
        """
        
        return self._generate_content(prompt)
    
    def _generate_content(self, prompt):
        """Generate content using the LLM based on the provided prompt."""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            st.error(f"Error generating document content: {str(e)}")
            return None
    
    def draft_document(self, doc_type, parameters):
        """
        Draft a legal document based on the specified type and parameters.
        
        Args:
            doc_type: Type of document to draft (e.g., "legal_memo", "legal_opinion")
            parameters: Dictionary of parameters for the document template
            
        Returns:
            Generated document content
        """
        template_func = self.templates.get(doc_type)
        
        if not template_func:
            st.error(f"Unknown document type: {doc_type}")
            return None
        
        return template_func(parameters)
    
    def generate_document_pdf(self, doc_type, parameters):
        """
        Generate a PDF document from a drafted legal document.
        
        Args:
            doc_type: Type of document to draft
            parameters: Dictionary of parameters for the document template
            
        Returns:
            Path to the generated PDF file
        """
        # Generate the document content
        content = self.draft_document(doc_type, parameters)
        
        if not content:
            return None
        
        # Generate a PDF based on the document type
        try:
            # Create a temporary file for the PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                pdf_path = temp_file.name
            
            # Get title and sections for the PDF
            title = parameters.get('subject', f"{doc_type.replace('_', ' ').title()}")
            
            if doc_type == "legal_memo":
                doc_type_name = "Legal Memorandum"
            elif doc_type == "legal_opinion":
                doc_type_name = "Legal Opinion"
            elif doc_type == "demand_letter":
                doc_type_name = "Demand Letter"
            elif doc_type == "contract_agreement":
                doc_type_name = "Contract Agreement"
            else:
                doc_type_name = doc_type.replace('_', ' ').title()
            
            # Create sections for the document
            sections = []
            
            # Add metadata section
            metadata = ""
            if doc_type == "legal_memo":
                metadata += f"TO: {parameters.get('recipient', '[Recipient]')}\n"
                metadata += f"FROM: {parameters.get('sender', '[Sender]')}\n"
                metadata += f"DATE: {parameters.get('date', datetime.now().strftime('%B %d, %Y'))}\n"
                metadata += f"SUBJECT: {parameters.get('subject', 'Legal Analysis')}\n"
            elif doc_type in ["legal_opinion", "demand_letter"]:
                metadata += f"DATE: {parameters.get('date', datetime.now().strftime('%B %d, %Y'))}\n"
                metadata += f"ADDRESSEE: {parameters.get('addressee', '[Recipient]')}\n"
                metadata += f"RE: {parameters.get('subject', 'Legal Matter')}\n"
            
            if metadata:
                sections.append({
                    "heading": "Document Information",
                    "content": metadata
                })
            
            # Add the main content
            sections.append({
                "heading": "Content",
                "content": content
            })
            
            # Generate the PDF
            pdf_path = create_custom_report(title, sections, doc_type=doc_type_name)
            
            return pdf_path
            
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return None
    
    def render_document_drafter_interface(self):
        """Render the document drafter interface in Streamlit."""
        st.subheader("Legal Document Drafter")
        st.write("Generate professionally formatted legal documents")
        
        # Document type selection
        doc_type = st.selectbox(
            "Document Type",
            ["legal_memo", "legal_opinion", "demand_letter", "contract_agreement"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Common parameters
        st.write("#### Document Parameters")
        date = st.date_input("Date", datetime.now()).strftime("%B %d, %Y")
        subject = st.text_input("Subject/Title")
        
        # Parameters specific to document type
        parameters = {
            'date': date,
            'subject': subject
        }
        
        if doc_type == "legal_memo":
            parameters['recipient'] = st.text_input("To")
            parameters['sender'] = st.text_input("From")
            parameters['issue'] = st.text_area("Issue")
            parameters['facts'] = st.text_area("Facts")
            
        elif doc_type in ["legal_opinion", "demand_letter"]:
            parameters['firm_name'] = st.text_input("Firm Name")
            parameters['addressee'] = st.text_area("Addressee")
            parameters['salutation'] = st.text_input("Salutation", "Sir/Madam")
            parameters['facts'] = st.text_area("Facts/Background")
            parameters['signature'] = st.text_input("Attorney Name")
            parameters['title'] = st.text_input("Title")
            
            if doc_type == "legal_opinion":
                parameters['questions'] = st.text_area("Legal Questions")
                
            elif doc_type == "demand_letter":
                parameters['demand'] = st.text_area("Demand")
        
        elif doc_type == "contract_agreement":
            parameters['title'] = st.text_input("Agreement Title")
            parameters['parties'] = st.text_area("Parties to the Agreement")
            parameters['terms'] = st.text_area("Key Terms")
            parameters['scope'] = st.text_area("Scope")
            parameters['compensation'] = st.text_area("Compensation (if applicable)")
            parameters['party1_name'] = st.text_input("First Party Name")
            parameters['party2_name'] = st.text_input("Second Party Name")
        
        # Generate document button
        if st.button("Generate Document"):
            with st.spinner("Drafting document... This may take a moment."):
                # Generate the document content
                content = self.draft_document(doc_type, parameters)
                
                if content:
                    # Display the generated content
                    st.success("Document drafted successfully!")
                    
                    with st.expander("Preview Document"):
                        st.markdown(content)
                    
                    # Generate and provide PDF download
                    pdf_path = self.generate_document_pdf(doc_type, parameters)
                    
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="Download Document as PDF",
                            data=pdf_bytes,
                            file_name=f"{doc_type}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
