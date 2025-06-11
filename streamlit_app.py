import streamlit as st
import os
import asyncio
import json
from typing import Dict, List, Any, Tuple
import google.generativeai as genai
from docx import Document
import re
import PyPDF2
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AM Auditor Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class ScoredItem:
    def __init__(self, category: str, item: str, score: int, justification: str, 
                 evidence: List[str] = None, improvement_guidance: str = None):
        self.category = category
        self.item = item
        self.score = score
        self.justification = justification
        self.evidence = evidence or []
        self.improvement_guidance = improvement_guidance

class AnalysisService:
    def __init__(self):
        self.model = None
        if "GEMINI_API_KEY" in st.secrets:
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                st.success("✅ Gemini AI initialized")
            except:
                st.warning("⚠️ Gemini initialization failed")
        else:
            st.info("📝 Using enhanced mock analysis")
    
    def _extract_text_from_pdf(self, pdf_file) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""
    
    def _extract_text_from_docx(self, docx_file) -> str:
        try:
            doc = Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
            return ""
    
    def _extract_names(self, transcript: str) -> Tuple[str, str, str]:
        """Extract business name, customer name, and agent name from transcript"""
        business_name = "Not identified"
        customer_name = "Not identified"
        agent_name = "Not identified"
        
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        
        # Enhanced patterns for Call Transcript headers
        for line in lines[:10]:
            # Pattern 1: "Call Transcript: Name (Role) & Name (Role, owner of Business)"
            if "Call Transcript:" in line:
                # Extract business name from "owner of [Business Name]" pattern
                owner_match = re.search(r'owner of ([A-Za-z][A-Za-z\s]{2,25})', line, re.IGNORECASE)
                if owner_match:
                    potential_business = owner_match.group(1).strip()
                    if self._is_valid_business_name(potential_business):
                        business_name = potential_business
                
                # Extract names from header
                header_match = re.search(
                    r'Call Transcript:\s*([A-Za-z\s]+)\s*\([^)]*(?:Manager|Agent|Representative)[^)]*\)\s*[&]\s*([A-Za-z\s]+)(?:\s*\([^)]*\))?',
                    line, re.IGNORECASE
                )
                if header_match:
                    agent_name = header_match.group(1).strip()
                    customer_name = header_match.group(2).strip()
                    break
                
                # Pattern 2: Simple header without roles
                simple_header = re.search(r'Call Transcript:\s*([A-Za-z\s]+)\s*&\s*([A-Za-z\s]+)', line, re.IGNORECASE)
                if simple_header:
                    agent_name = simple_header.group(1).strip()
                    customer_name = simple_header.group(2).strip()
                    break
        
        # Extract business name from conversation content if not found in header
        if business_name == "Not identified":
            business_patterns = [
                # "speaking with [Name] from [Business Name]"
                r"speaking with .+ from\s+([A-Za-z][A-Za-z\s]{2,25})",
                # "I'm calling from [Business Name]"
                r"(?:calling|speaking|I'm)\s+from\s+([A-Za-z][A-Za-z\s]{2,20})",
                # "This is [Name] from [Business Name]"
                r"This is .+ from\s+([A-Za-z][A-Za-z\s]{2,20})",
                # "representing [Business Name]"
                r"representing\s+([A-Za-z][A-Za-z\s]{2,20})",
                # "at [Business Name]" or "your [Business Name]"
                r"(?:at|your)\s+([A-Za-z][A-Za-z\s]{2,20})(?:\s+(?:outlet|shop|store|business|restaurant|cafe))?",
            ]
            
            for line in lines[:15]:
                for pattern in business_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        potential_business = match.group(1).strip()
                        
                        # Validate business name
                        if self._is_valid_business_name(potential_business):
                            business_name = potential_business
                            break
                
                if business_name != "Not identified":
                    break
        
        # If no business name found from patterns, try to extract from speaker identification
        if business_name == "Not identified":
            for line in lines[:10]:
                speaker_match = re.match(r'^([A-Za-z\s]+):\s*(.+)', line)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    content = speaker_match.group(2).lower()
                    
                    # If speaker mentions being from somewhere
                    if "from" in content:
                        from_match = re.search(r'from\s+([A-Za-z][A-Za-z\s]{2,20})', content, re.IGNORECASE)
                        if from_match:
                            potential_business = from_match.group(1).strip()
                            if self._is_valid_business_name(potential_business):
                                business_name = potential_business
                                break
        
        # Clean up names
        business_name = self._clean_name(business_name)
        customer_name = self._clean_name(customer_name)
        agent_name = self._clean_name(agent_name)
        
        return business_name, customer_name, agent_name
    
    def _is_valid_business_name(self, name: str) -> bool:
        """Validate if extracted name is a valid business name"""
        if not name or len(name.strip()) < 3:
            return False
        
        name_lower = name.lower().strip()
        
        # Invalid business names (including StoreHub variations)
        invalid_names = [
            'storehub', 'store', 'hub', 'calling', 'speaking', 'the', 'from',
            'account', 'manager', 'representative', 'customer', 'service',
            'support', 'team', 'hello', 'good', 'morning', 'afternoon',
            'evening', 'thank', 'thanks', 'you', 'yes', 'no', 'okay',
            'sure', 'please', 'sorry', 'help', 'assistance'
        ]
        
        # Check if it's an invalid name
        if name_lower in invalid_names:
            return False
        
        # Check if it contains only invalid words
        words = name_lower.split()
        if all(word in invalid_names for word in words):
            return False
        
        # Must contain at least one alphabetic character
        if not any(c.isalpha() for c in name):
            return False
        
        return True
    
    def _clean_name(self, name: str) -> str:
        """Clean and format extracted name"""
        if not name or name == "Not identified":
            return "Not identified"
        
        # Remove extra whitespace and capitalize properly
        cleaned = ' '.join(name.split()).title()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Sir', 'Madam']
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix + ' '):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned if cleaned else "Not identified"
    
    async def analyze_conversation(self, transcript: str) -> Dict[str, Any]:
        business_name, customer_name, agent_name = self._extract_names(transcript)
        
        # Content analysis
        transcript_lower = transcript.lower()
        has_greeting = any(word in transcript_lower for word in ['hello', 'hi', 'good morning', 'thanks'])
        has_profanity = any(word in transcript_lower for word in ['damn', 'shit', 'stupid'])
        has_service = any(word in transcript_lower for word in ['problem', 'issue', 'help', 'support'])
        has_sales = any(word in transcript_lower for word in ['product', 'offer', 'solution'])
        has_questions = '?' in transcript
        
        scored_items = []
        
        # Rapport Building
        if has_profanity:
            rapport_score = 1
            rapport_justification = "TERMINATION CANDIDATE: Unprofessional language detected."
        elif has_greeting:
            rapport_score = 3
            rapport_justification = "MEDIOCRE: Basic greeting present but lacks sophistication."
        else:
            rapport_score = 2
            rapport_justification = "CONCERNING: Weak rapport establishment."
        
        scored_items.append(ScoredItem(
            category="Core Communication Fundamentals",
            item="Rapport Building & Sincerity",
            score=rapport_score,
            justification=rapport_justification,
            evidence=["Greeting detected" if has_greeting else "No proper greeting"],
            improvement_guidance="Use warm, courteous language and show genuine concern."
        ))
        
        # Active Listening
        listening_score = 4 if has_questions else 2
        scored_items.append(ScoredItem(
            category="Core Communication Fundamentals",
            item="Active Listening",
            score=listening_score,
            justification="SOLID: Questions present." if has_questions else "POOR: No evidence of listening.",
            evidence=["Questions found" if has_questions else "No clarifying questions"],
            improvement_guidance="Ask clarifying questions and paraphrase concerns."
        ))
        
        # Professional Communication
        if has_profanity:
            prof_score = 1
            prof_justification = "TERMINATION: Profanity unacceptable."
        elif has_greeting and has_questions:
            prof_score = 4
            prof_justification = "SOLID: Professional standards maintained."
        else:
            prof_score = 2
            prof_justification = "CONCERNING: Basic professionalism only."
        
        scored_items.append(ScoredItem(
            category="Core Communication Fundamentals",
            item="Professional Communication",
            score=prof_score,
            justification=prof_justification,
            evidence=["Professional tone maintained" if prof_score >= 3 else "Issues detected"],
            improvement_guidance="Maintain professional tone and courteous language."
        ))
        
        # Conversation type
        if has_service and has_sales:
            conv_type = "mixed"
            subject = f"{business_name} - Mixed - Support & Sales"
        elif has_service:
            conv_type = "servicing"
            subject = f"{business_name} - Servicing - Issue Resolution"
        else:
            conv_type = "consultation"
            subject = f"{business_name} - Consultation - Product Discussion"
        
        total_score = round(sum(item.score for item in scored_items) / len(scored_items) * 20)
        
        return {
            "participant_info": {
                "business_name": business_name,
                "customer_name": customer_name,
                "agent_name": agent_name
            },
            "summary": {
                "conversation_type": conv_type,
                "subject": subject,
                "total_score": total_score,
                "pass_status": total_score >= 80,
                "key_strengths": ["Professional communication"] if prof_score >= 3 else [],
                "areas_for_improvement": ["Improve rapport building", "Enhance active listening"],
                "action_plan": ["Practice warm greetings", "Ask more questions", "Show empathy"]
            },
            "scored_items": scored_items,
            "coaching_summary": f"Dr. Harrington's Assessment: Score {total_score}/100. {'ACCEPTABLE performance but room for improvement' if total_score >= 60 else 'NEEDS IMMEDIATE IMPROVEMENT'}. Focus on building stronger client relationships and demonstrating active listening."
        }

@st.cache_resource
def get_analysis_service():
    return AnalysisService()

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 AM Auditor Pro</h1>
        <p>AI-powered conversation analysis with Dr. Victoria "The Decimator" Harrington</p>
        <p><em>Brutal honesty for elite performance</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload Conversation")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx'],
            help="Upload conversation transcript, PDF, or Word document"
        )
        
        st.subheader("💬 Or Paste Text")
        manual_text = st.text_area(
            "Paste conversation transcript",
            height=200,
            placeholder="Paste your conversation transcript here..."
        )
        
        analyze_button = st.button("🔍 Analyze Conversation", type="primary")
        
        st.markdown("---")
        st.markdown("""
        ### 📋 Instructions
        1. Upload a file or paste text
        2. Click "Analyze Conversation"
        3. Review brutal assessment
        
        ### 📊 Scoring Scale
        - **5**: PERFECTION
        - **4**: BARELY ACCEPTABLE
        - **3**: MEDIOCRE
        - **2**: CONCERNING
        - **1**: TERMINATION CANDIDATE
        """)
    
    # Main content
    if analyze_button:
        transcript = ""
        
        if uploaded_file is not None:
            analysis_service = get_analysis_service()
            
            if uploaded_file.type == "text/plain":
                transcript = str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type == "application/pdf":
                transcript = analysis_service._extract_text_from_pdf(uploaded_file)
            elif "wordprocessingml" in uploaded_file.type:
                transcript = analysis_service._extract_text_from_docx(uploaded_file)
            else:
                st.error("Unsupported file type")
                return
                
        elif manual_text.strip():
            transcript = manual_text.strip()
        else:
            st.warning("Please upload a file or paste text")
            return
        
        if not transcript:
            st.error("No text found")
            return
        
        # Analysis
        with st.spinner("🔍 Dr. Harrington is analyzing..."):
            analysis_service = get_analysis_service()
            
            # Debug: Show name extraction results
            with st.expander("🔍 Debug: Name Extraction", expanded=False):
                business, customer, agent = analysis_service._extract_names(transcript)
                st.write(f"**Business**: {business}")
                st.write(f"**Customer**: {customer}")
                st.write(f"**Agent**: {agent}")
                
                # Show first 10 lines for debugging
                lines = [line.strip() for line in transcript.split('\n') if line.strip()]
                st.write("**First 10 lines of transcript:**")
                for i, line in enumerate(lines[:10], 1):
                    st.write(f"{i}. {line}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(analysis_service.analyze_conversation(transcript))
            loop.close()
        
        st.success("✅ Analysis Complete!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score = results['summary']['total_score']
            st.metric("📊 Overall Score", f"{score}/100", 
                     delta="PASS" if results['summary']['pass_status'] else "FAIL")
        
        with col2:
            st.metric("🏢 Business", results['participant_info']['business_name'])
        
        with col3:
            st.metric("👤 Customer", results['participant_info']['customer_name'])
        
        with col4:
            st.metric("👨‍💼 Agent", results['participant_info']['agent_name'])
        
        # Details
        st.subheader("📋 Conversation Details")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Type:** {results['summary']['conversation_type'].title()}")
        with col2:
            st.info(f"**Subject:** {results['summary']['subject']}")
        
        # Score breakdown
        st.subheader("📈 Detailed Score Breakdown")
        
        categories = {}
        for item in results['scored_items']:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        for category, items in categories.items():
            st.markdown(f"### {category}")
            for item in items:
                with st.expander(f"⭐ {item.item} - Score: {item.score}/5"):
                    st.markdown(f"**Assessment:** {item.justification}")
                    if item.evidence:
                        st.markdown("**Evidence:**")
                        for evidence in item.evidence:
                            st.info(evidence)
                    if item.improvement_guidance:
                        st.warning(f"**Guidance:** {item.improvement_guidance}")
        
        # Insights
        col1, col2 = st.columns(2)
        
        with col1:
            if results['summary']['key_strengths']:
                st.subheader("💪 Strengths")
                for strength in results['summary']['key_strengths']:
                    st.success(f"✅ {strength}")
        
        with col2:
            if results['summary']['areas_for_improvement']:
                st.subheader("🎯 Improvements")
                for area in results['summary']['areas_for_improvement']:
                    st.error(f"❌ {area}")
        
        # Action plan
        if results['summary']['action_plan']:
            st.subheader("📋 Action Plan")
            for i, action in enumerate(results['summary']['action_plan'], 1):
                st.markdown(f"{i}. {action}")
        
        # Assessment
        st.subheader("💬 Dr. Harrington's Assessment")
        st.error(results['coaching_summary'])
        
        # Transcript
        with st.expander("📄 View Transcript"):
            st.text_area("Original Transcript", transcript, height=300, disabled=True)
        
    else:
        # Welcome
        st.markdown("""
        ## Welcome to AM Auditor Pro! 👋
        
        Upload a conversation transcript or paste text to get Dr. Victoria "The Decimator" Harrington's brutal assessment.
        
        ### What You'll Get:
        - 🎯 **Brutal Scoring** (1-5 scale)
        - 📊 **Performance Score** and pass/fail
        - 👥 **Participant ID** (business, customer, agent)
        - 📈 **Detailed Breakdown** with evidence
        - 💬 **Coaching Summary** with actions
        
        ### Supported Files:
        - 📄 Text files (.txt)
        - 📑 PDF documents (.pdf)
        - 📝 Word documents (.docx)
        - 💬 Manual text input
        
        Start by uploading a file or pasting text! 🚀
        """)

if __name__ == "__main__":
    main()
