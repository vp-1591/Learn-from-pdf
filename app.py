import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import os
import gspread
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- CONSTANTS ---
LOCAL_GSPREAD_KEY_FILE = "lfpdf-479215-51af785aa8fa.json"

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AutoStudy AI", page_icon="🧠", layout="wide")

# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- CSS STYLING (STREAMLIT NATIVE THEMING) ---

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Global Font */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero Section Styling */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #4F46E5, #9333EA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        text-align: center;
        opacity: 0.7;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Magic Wand Button Icon Styling */
    div.stButton > button[aria-label="Generate"] {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%; 
        height: 100%;
        min-height: 45px;
        padding: 0;
        color: transparent !important;
    }

    div.stButton > button[aria-label="Generate"]::before {
        content: "";
        width: 24px;
        height: 24px;
        background-color: currentColor;
        mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M15 4V2'/><path d='M15 16v-2'/><path d='M8 9h2'/><path d='M20 9h2'/><path d='M17.8 11.8L19 13'/><path d='M15 9l-1 1'/><path d='M17.8 6.2L19 5'/><path d='M3 21l9-9'/><path d='M12.2 6.2L11 5'/></svg>");
        -webkit-mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M15 4V2'/><path d='M15 16v-2'/><path d='M8 9h2'/><path d='M20 9h2'/><path d='M17.8 11.8L19 13'/><path d='M15 9l-1 1'/><path d='M17.8 6.2L19 5'/><path d='M3 21l9-9'/><path d='M12.2 6.2L11 5'/></svg>");
        mask-size: contain;
        -webkit-mask-size: contain;
        mask-repeat: no-repeat;
        -webkit-mask-repeat: no-repeat;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

@st.cache_resource
def get_gspread_client():
    """
    Initializes the Gspread client with conditional authentication.
    Checks Streamlit secrets first, then local file.
    """
    try:
        # 1. Check Cloud/Secrets First
        try:
            if 'gspread' in st.secrets:
                return gspread.service_account_from_dict(st.secrets['gspread'])
        except Exception:
            pass
        
        # 2. Check Local File Second
        if os.path.exists(LOCAL_GSPREAD_KEY_FILE):
            return gspread.service_account(filename=LOCAL_GSPREAD_KEY_FILE)
        
        else:
            st.warning("Internal Error. Feedback will not be saved.")
            return None
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

def submit_feedback(rating, comment):
    """
    Submits feedback to Google Sheets.
    """
    client = get_gspread_client()
    if not client:
        return False
    try:
        # Open the spreadsheet
        sheet_name = os.getenv("SHEET_NAME")
            
        # Fallback default
        if not sheet_name:
            sheet_name = "LearnFromPDF_Feedback"
        
        # Open the sheet - handle potential errors if sheet doesn't exist
        try:
            sh = client.open(sheet_name)
        except gspread.SpreadsheetNotFound:
             # Create if it doesn't exist (optional, but good for first run)
             try:
                sh = client.create(sheet_name)
                sh.share(client.auth.service_account_email, perm_type='user', role='owner')
             except:
                 return False

        worksheet = sh.get_worksheet(0)

        # Append row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Use a simple session ID or generate one if not present
        if 'session_id' not in st.session_state:
            import uuid
            st.session_state['session_id'] = str(uuid.uuid4())
        
        session_id = st.session_state['session_id']
        
        worksheet.append_row([timestamp, rating, comment, session_id])
        return True
        
    except Exception as e:
        return False

def extract_text_from_pdf(pdf_file):
    """
    Extracts text from an uploaded PDF file.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def generate_study_material(text_content, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})

        prompt = f"""
        You must generate all output text in the same language detected in the "TEXT TO ANALYZE" section.
        
        You are an expert educational AI. Analyze the provided text and extract 4 to 8 distinct, key concepts.
        
        TEXT TO ANALYZE:
        {text_content[:50000]}
        
        OUTPUT FORMAT (JSON ARRAY):
        [
            {{
                "title": "Concept Title",
                "summary": "A 1-3 sentence summary of the concept."
            }},
            ...
        ]
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

async def generate_chat_response(concept_title, concept_summary, user_prompt, pdf_text, api_key):
    """
    Handles chat for a specific concept with history management.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Get history for this concept
        history = st.session_state['chat_histories'].get(concept_title, [])
        
        # Initialize if empty
        if not history:
            system_instruction = f"""
            You are a helpful, Socratic tutor specializing in the concept: '{concept_title}'.
            
            Concept Summary: {concept_summary}
            
            Full Context (Reference Only):
            {pdf_text[:30000]}
            
            Your goal is to help the user understand '{concept_title}' deeply. Answer questions, provide examples, and ask guiding questions.
            Keep responses concise and conversational.
            """
            history.append({"role": "user", "parts": [system_instruction]})
        
        # Summarization/Pruning if history is too long (keep system prompt + last few)
        if len(history) > 10:
            # Simple pruning for now to save tokens, keeping system prompt and last 4
            history = [history[0]] + history[-4:]
            
        # Add user message
        history.append({"role": "user", "parts": [user_prompt]})
        
        # Generate response
        response = await model.generate_content_async(history)
        
        # Add model response
        history.append({"role": "model", "parts": [response.text]})
        
        # Update state
        st.session_state['chat_histories'][concept_title] = history
        
        return response.text
        
    except Exception as e:
        return f"Error: {e}"

def process_generation(uploaded_file, api_key, status_container=None):
    """
    Handles the generation logic for PDF files.
    """
    msg_container = status_container if status_container else st

    if not api_key:
        msg_container.warning("API Key missing. Please enter it above.")
        return

    if not uploaded_file:
        msg_container.warning("Please upload a PDF file first.")
        return

    # Execute spinner and messages within the container context
    with msg_container:
        with st.spinner("Reading PDF & Generating content..."):
            # 1. Extract Text
            text_to_process = extract_text_from_pdf(uploaded_file)
            
            if not text_to_process:
                st.error("Could not extract text from the PDF. It might be empty or scanned.")
                return

            st.session_state['study_material'] = text_to_process

            # 2. Generate Study Material
            data = generate_study_material(text_to_process, api_key)
            if data:
                st.session_state['generated_data'] = data
                st.session_state['pdf_text'] = text_to_process
                st.session_state['chat_histories'] = {}
                st.session_state['show_feedback'] = True
                st.session_state['feedback_submitted'] = False
                st.rerun()

# --- MAIN APP UI ---

# Header Layout (Centered Title Only)
st.markdown('<div class="hero-title">Learn From PDF</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI Study Kit: Instantly convert your PDF lecture slides and papers into summaries.</div>', unsafe_allow_html=True)

# API Key Handling
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.warning("⚠️ Google Gemini API Key is missing. Please enter it below to proceed.")
    api_key = st.text_input("Enter Google Gemini API Key", type="password", key="api_key_runtime_input")

# --- SESSION STATE INITIALIZATION ---
if 'study_material' not in st.session_state:
    st.session_state['study_material'] = ""
if 'generated_data' not in st.session_state:
    st.session_state['generated_data'] = None
if 'show_feedback' not in st.session_state:
    st.session_state['show_feedback'] = False
if 'feedback_submitted' not in st.session_state:
    st.session_state['feedback_submitted'] = False
if 'chat_histories' not in st.session_state:
    st.session_state['chat_histories'] = {}
if 'pdf_text' not in st.session_state:
    st.session_state['pdf_text'] = ""

# --- WIDGETS ---
# Centered Card Container for Inputs
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.container(border=True):
        # Single Row: Uploader + Button
        u_col1, u_col2 = st.columns([5, 1])
        
        with u_col1:
            uploaded_file = st.file_uploader(
                "Upload PDF",
                type=["pdf"],
                label_visibility="collapsed"
            )
        
        with u_col2:
            # Spacer to align button with the file uploader box
            st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True) 
            # Use label="Generate" to match CSS selector, but CSS will hide text and show icon
            generate_clicked = st.button("Generate", key="btn_pdf_gen", type="primary", use_container_width=True)

        # Status Container
        status_container = st.container()

        if generate_clicked:
            process_generation(uploaded_file, api_key, status_container=status_container)

# --- DISPLAY RESULTS ---
data = st.session_state.get('generated_data')
if data:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Study Concepts")
    
    # Iterate over concepts
    for i, concept in enumerate(data):
        title = concept.get('title', f"Concept {i+1}")
        summary = concept.get('summary', "No summary available.")
        
        # Concept Card Style
        with st.expander(f"**{i+1}. {title}**", expanded=False):
            st.markdown(f"_{summary}_")
            st.markdown("---")
            
            # Chat Interface for this concept
            st.markdown("#### Discuss this concept")
            
            # Container for chat history
            chat_container = st.container()
            
            # Get history
            history = st.session_state['chat_histories'].get(title, [])
            
            # Display history (skip system prompt)
            with chat_container:
                for msg in history:
                    if msg['role'] == 'user' and "You are a helpful" in msg['parts'][0]:
                        continue # Skip system prompt
                    
                    role_display = "user" if msg['role'] == 'user' else "assistant"
                    with st.chat_message(role_display):
                        st.write(msg['parts'][0])
            
            # Chat Input
            if prompt := st.chat_input(f"Ask about {title}...", key=f"chat_input_{i}"):
                # Add user message immediately to UI
                with chat_container:
                    with st.chat_message("user"):
                        st.write(prompt)
                
                # Generate response
                with st.spinner("Thinking..."):
                    response_text = asyncio.run(generate_chat_response(
                        title, 
                        summary, 
                        prompt, 
                        st.session_state['pdf_text'],
                        api_key
                    ))
                
                # Rerun to update history display properly
                st.rerun()

# --- FEEDBACK SECTION ---
if st.session_state.get('show_feedback'):
    st.markdown("---")
    if st.session_state.get('feedback_submitted'):
         st.success("Thank you for your feedback!")
    else:
        with st.expander("Share Feedback"):
            # Placeholder for feedback submission status
            feedback_status = st.empty()
            
            with st.form("feedback_form"):
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Comments")
                submitted = st.form_submit_button("Submit")
                
                if submitted:
                    # Show loading message
                    with feedback_status:
                        with st.spinner("Submitting your feedback..."):
                            # Submit feedback
                            success = submit_feedback(rating, comment)
                    
                    if success:
                        st.session_state['feedback_submitted'] = True
                        st.rerun()
                    else:
                        feedback_status.error("Failed to submit feedback. Please try again.")