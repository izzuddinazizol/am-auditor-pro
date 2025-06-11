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
from io import BytesIO

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
        """
        3-Step AI Analysis Process:
        1. Extract participant info and conversation basics
        2. Strict rubric-based evaluation with merciless standards
        3. Elite success manager coaching with specific action plans
        """
        
        # STEP 1: Extract Participant Info and Conversation Basics
        extraction_prompt = f"""
You are an expert conversation analyst. Analyze this transcript and extract key information.

TRANSCRIPT:
{transcript}

Extract the following information in JSON format:
{{
    "business_name": "Customer's business name (NEVER StoreHub)",
    "customer_name": "Customer's name",
    "agent_name": "Account manager/agent name",
    "conversation_type": "consultation/servicing/mixed",
    "main_theme": "Main topic in exactly 5 words or less"
}}

RULES:
- Business name should be the CUSTOMER'S business, never StoreHub
- Conversation type: consultation (sales/product discussion), servicing (support/issues), mixed (both)
- Main theme: capture the core purpose in 5 words maximum
- Use "Not identified" if information cannot be found
- Be precise and accurate

Respond with ONLY the JSON, no other text.
"""

        try:
            if self.model:
                # Get participant info from Gemini
                response = self.model.generate_content(extraction_prompt)
                participant_data = json.loads(response.text.strip())
            else:
                raise Exception("Gemini model not available")
        except Exception as e:
            st.warning(f"Using local extraction (Gemini unavailable): {str(e)}")
            # Fallback to local extraction if Gemini fails
            business_name, customer_name, agent_name = self._extract_names(transcript)
            participant_data = {
                "business_name": business_name,
                "customer_name": customer_name, 
                "agent_name": agent_name,
                "conversation_type": "consultation",
                "main_theme": "General discussion"
            }

        # STEP 2: Strict Rubric-Based Evaluation
        evaluation_prompt = f"""
You are Dr. Victoria "The Decimator" Harrington, the most ruthless conversation analyst in the industry. You have ZERO TOLERANCE for mediocrity.

CONVERSATION TRANSCRIPT:
{transcript}

EVALUATION RUBRIC - Score each item 1-5 (5=PERFECTION, 4=BARELY ACCEPTABLE, 3=MEDIOCRE, 2=CONCERNING, 1=TERMINATION CANDIDATE):

**Core Communication Fundamentals:**
1. Rapport Building & Sincerity - Building genuine connection and trust
2. Active Listening - Demonstrating understanding and engagement  
3. Professional Communication - Maintaining appropriate tone and language

**Solution-Oriented Approach:**
4. Problem Identification - Accurately identifying customer needs/issues
5. Solution Presentation - Clearly explaining solutions and benefits
6. Objection Handling - Addressing concerns professionally

**Customer Experience Excellence:**
7. Empathy & Understanding - Showing genuine care for customer situation
8. Responsiveness - Timely and relevant responses to customer needs
9. Follow-up & Commitment - Ensuring customer satisfaction and next steps

CRITICAL RULE: If ANY unprofessional or rude language is detected, immediately score 1 across ALL rubrics.

Provide your analysis in this JSON format:
{{
    "overall_score": 0-100,
    "pass_status": true/false,
    "scored_items": [
        {{
            "category": "Category name",
            "item": "Item name", 
            "score": 1-5,
            "justification": "Your brutal assessment",
            "evidence": ["Specific quotes from transcript"],
            "improvement_guidance": "What needs to be fixed"
        }}
    ],
    "key_strengths": ["List strengths if score ≥4"],
    "areas_for_improvement": ["List critical weaknesses"],
    "brutal_assessment": "Your merciless overall judgment"
}}

Be RUTHLESS. Demand EXCELLENCE. Show NO MERCY for substandard performance.
"""

        # Get evaluation from Gemini
        try:
            if self.model:
                eval_response = self.model.generate_content(evaluation_prompt)
                evaluation_data = json.loads(eval_response.text.strip())
            else:
                raise Exception("Gemini model not available")
        except Exception as e:
            st.warning(f"Using basic evaluation (Gemini unavailable): {str(e)}")
            # Fallback evaluation
            evaluation_data = {
                "overall_score": 60,
                "pass_status": False,
                "scored_items": [
                    {
                        "category": "Core Communication Fundamentals",
                        "item": "Basic Assessment",
                        "score": 3,
                        "justification": "Basic analysis performed - Gemini AI unavailable",
                        "evidence": ["Transcript processed"],
                        "improvement_guidance": "Full AI analysis requires Gemini API key"
                    }
                ],
                "key_strengths": ["Conversation completed"],
                "areas_for_improvement": ["Enable full AI analysis"],
                "brutal_assessment": "Basic analysis - Enable Gemini AI for full assessment"
            }

        # STEP 3: Elite Success Manager Coaching
        coaching_prompt = f"""
You are now the world's #1 Chief Success Officer and elite success manager trainer. You drive revenue and deliver world-class customer experiences.

CONVERSATION ANALYSIS:
- Business: {participant_data['business_name']}
- Customer: {participant_data['customer_name']}  
- Agent: {participant_data['agent_name']}
- Type: {participant_data['conversation_type']}
- Theme: {participant_data['main_theme']}

EVALUATION RESULTS:
{json.dumps(evaluation_data, indent=2)}

TRANSCRIPT:
{transcript}

For any items scored <4, provide SPECIFIC, ACTIONABLE coaching:

Create detailed action plans in JSON format:
{{
    "coaching_summary": "Your expert coaching assessment",
    "specific_action_plans": [
        {{
            "area": "Area needing improvement",
            "current_issue": "What went wrong",
            "specific_actions": [
                "Specific action 1",
                "Specific action 2", 
                "Specific action 3"
            ],
            "practice_scripts": ["Example phrases to use"],
            "success_metrics": "How to measure improvement"
        }}
    ],
    "immediate_priorities": ["Top 3 things to fix immediately"],
    "long_term_development": ["Strategic improvements for sustained success"]
}}

Be SPECIFIC. Provide EXACT phrases, CONCRETE examples, and MEASURABLE outcomes.
Focus on revenue impact and customer experience excellence.
"""

        # Get coaching from Gemini
        try:
            if self.model:
                coaching_response = self.model.generate_content(coaching_prompt)
                coaching_data = json.loads(coaching_response.text.strip())
            else:
                raise Exception("Gemini model not available")
        except Exception as e:
            st.warning(f"Using basic coaching (Gemini unavailable): {str(e)}")
            # Fallback coaching
            coaching_data = {
                "coaching_summary": "Basic coaching - Full AI coaching requires Gemini API key",
                "specific_action_plans": [],
                "immediate_priorities": ["Enable Gemini AI for detailed coaching"],
                "long_term_development": ["Integrate full AI analysis capabilities"]
            }

        # Combine all results
        final_results = {
            "participant_info": {
                "business_name": participant_data.get("business_name", "Not identified"),
                "customer_name": participant_data.get("customer_name", "Not identified"),
                "agent_name": participant_data.get("agent_name", "Not identified")
            },
            "summary": {
                "conversation_type": participant_data.get("conversation_type", "consultation"),
                "subject": f"{participant_data.get('business_name', 'Unknown')} - {participant_data.get('conversation_type', 'consultation').title()} - {participant_data.get('main_theme', 'Discussion')}",
                "total_score": evaluation_data.get("overall_score", 0),
                "pass_status": evaluation_data.get("pass_status", False),
                "key_strengths": evaluation_data.get("key_strengths", []),
                "areas_for_improvement": evaluation_data.get("areas_for_improvement", []),
                "action_plan": coaching_data.get("immediate_priorities", [])
            },
            "scored_items": [
                ScoredItem(
                    category=item.get("category", "Unknown"),
                    item=item.get("item", "Unknown"),
                    score=item.get("score", 1),
                    justification=item.get("justification", "No assessment"),
                    evidence=item.get("evidence", []),
                    improvement_guidance=item.get("improvement_guidance", "")
                ) for item in evaluation_data.get("scored_items", [])
            ],
            "coaching_summary": evaluation_data.get("brutal_assessment", "Analysis completed"),
            "detailed_coaching": coaching_data
        }

        return final_results

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
        
        # Elite Success Manager Coaching
        if 'detailed_coaching' in results and results['detailed_coaching']:
            st.subheader("🏆 Elite Success Manager Coaching")
            coaching = results['detailed_coaching']
            
            # Coaching Summary
            if 'coaching_summary' in coaching:
                st.info(f"**Expert Assessment:** {coaching['coaching_summary']}")
            
            # Specific Action Plans
            if 'specific_action_plans' in coaching and coaching['specific_action_plans']:
                st.markdown("### 🎯 Detailed Action Plans")
                for i, plan in enumerate(coaching['specific_action_plans'], 1):
                    with st.expander(f"Action Plan {i}: {plan.get('area', 'Improvement Area')}"):
                        st.markdown(f"**Current Issue:** {plan.get('current_issue', 'Not specified')}")
                        
                        if 'specific_actions' in plan and plan['specific_actions']:
                            st.markdown("**Specific Actions:**")
                            for j, action in enumerate(plan['specific_actions'], 1):
                                st.markdown(f"{j}. {action}")
                        
                        if 'practice_scripts' in plan and plan['practice_scripts']:
                            st.markdown("**Practice Scripts:**")
                            for script in plan['practice_scripts']:
                                st.code(script, language=None)
                        
                        if 'success_metrics' in plan:
                            st.markdown(f"**Success Metrics:** {plan['success_metrics']}")
            
            # Immediate Priorities
            if 'immediate_priorities' in coaching and coaching['immediate_priorities']:
                st.markdown("### 🚨 Immediate Priorities")
                for i, priority in enumerate(coaching['immediate_priorities'], 1):
                    st.error(f"{i}. {priority}")
            
            # Long-term Development
            if 'long_term_development' in coaching and coaching['long_term_development']:
                st.markdown("### 📈 Long-term Development")
                for i, development in enumerate(coaching['long_term_development'], 1):
                    st.success(f"{i}. {development}")
        
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
