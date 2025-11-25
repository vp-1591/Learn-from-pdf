import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import os
import gspread
from datetime import datetime
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

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Global Theme */
    .stApp {
        background-color: #f4f6f8;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
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
        color: #64748b;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Floating Card Container Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
        padding: 20px;
    }

    /* Index Card Styling for Summary */
    .summary-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        border: 1px solid #e2e8f0;
    }
    .summary-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .summary-number {
        color: #4F46E5;
        font-weight: 700;
        font-size: 1.1em;
        margin-bottom: 8px;
        display: block;
    }

    /* Quiz Card Styling */
    .quiz-container {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #6C63FF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Spinner Text */
    .stSpinner > div > div {
        color: #4F46E5;
        font-weight: 600;
    }

    /* --- DARK MODE SUPPORT --- */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        h1, h2, h3 {
            color: #F0F2F6;
        }
        .hero-subtitle {
            color: #BFC5D3;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1F242C;
            border: 1px solid #384455;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .summary-card {
            background-color: #1F242C;
            border: 1px solid #384455;
            color: #E0E0E0;
            box-shadow: none;
        }
        .summary-card:hover {
            background-color: #262B33;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .summary-number {
            color: #818CF8;
        }
        .quiz-container {
            background-color: #1F242C;
            border-left: 5px solid #818CF8;
            color: #E0E0E0;
            box-shadow: none;
        }
        p, li, span {
            color: #E0E0E0;
        }
    }

    /* --- MAGIC WAND BUTTON STYLING (SPECIFIC TARGETING) --- */
    /* Target buttons that contain the specific icon-only logic via aria-label */
    div.stButton > button[aria-label="Generate"] {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%; 
        height: 100%;
        min-height: 45px; /* Match input height roughly */
        padding: 0;
        color: transparent !important; /* Hide text */
    }

    /* Inject SVG icon using mask-image for currentColor support */
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

    /* --- CUSTOM FEEDBACK SUCCESS BOX --- */
    .success-box {
        background-color: #dcfce7; /* Green-100 */
        border: 1px solid #86efac; /* Green-300 */
        color: #166534; /* Green-800 */
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        position: relative;
        font-weight: 500;
    }

    /* --- POSITIONING THE DISMISS BUTTON (SUCCESS) --- */
    /* Target the button with label '✖' (Heavy Multiplication X) */
    button[aria-label="✖"] {
        position: absolute !important;
        top: -55px !important; /* Pull it up into the box (adjust based on box height) */
        right: 10px !important;
        background: transparent !important;
        border: none !important;
        color: #166534 !important;
        font-size: 1.2rem !important;
        z-index: 100;
    }
    button[aria-label="✖"]:hover {
        color: #b91c1c !important;
        background-color: rgba(255,255,255,0.5) !important;
    }

    /* --- POSITIONING THE CARD CLOSE BUTTON --- */
    /* Target the button with label '✕' (Multiplication X) */
    button[aria-label="✕"] {
        border: none !important;
        background: transparent !important;
        color: #64748b !important;
        font-size: 1.2rem !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex;
        justify-content: flex-end;
    }
    button[aria-label="✕"]:hover {
        color: #ef4444 !important;
        background: transparent !important;
    }
    
    /* Force right alignment for the card close button container */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        display: flex;
        justify-content: flex-end;
    }

</style>
""", unsafe_allow_html=True)

# --- API KEY LOGIC ---
api_key = None
# Try to get API key from secrets first
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

# If not in secrets, try environment variable (loaded by dotenv)
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

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

            if "GSPREAD_AUTH" in st.secrets:
                return gspread.service_account_from_dict(st.secrets["GSPREAD_AUTH"])
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
        return

    try:
        # Open the spreadsheet
        sheet_name = None
        
        # 1. Try Secrets
        try:
            sheet_name = st.secrets.get("SHEET_NAME")
        except Exception:
            pass
        
        # 2. Try Environment Variable if not in secrets
        if not sheet_name:
            sheet_name = os.getenv("SHEET_NAME")
            
        # 3. Fallback default
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
                 st.error(f"Spreadsheet '{sheet_name}' not found and could not be created.")
                 return

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
        st.error(f"Error saving feedback: {e}")
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
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        You are an expert educational AI. Analyze the text and produce structured study content.
        
        TEXT TO ANALYZE:
        {text_content[:30000]}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "summary_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
            "flashcards": [
                {{"question": "Question?", "answer": "Answer"}}
            ],
            "quiz": [
                {{"question": "Question?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}}
            ]
        }}
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

def process_generation(uploaded_file, status_container=None):
    """
    Handles the generation logic for PDF files.
    """
    msg_container = status_container if status_container else st

    if not api_key:
        msg_container.warning("API Key missing. Please enter it in the sidebar.")
        return

    if not uploaded_file:
        msg_container.warning("Please upload a PDF file first.")
        return

    # Execute spinner and messages within the container context
    with msg_container:
        with st.spinner("✨ Reading PDF & Generating content..."):
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
                st.session_state['show_feedback'] = True # Enable feedback on success
                st.session_state['feedback_submitted'] = False # Reset submission state
                st.rerun() # Rerun to display results

# --- MAIN APP UI ---

# Hero Section
st.markdown('<div class="hero-title">Learn From PDF</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI Study Kit: Instantly convert your PDF lecture slides and papers into summaries, flashcards, and quizzes.</div>', unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'study_material' not in st.session_state:
    st.session_state['study_material'] = ""
if 'generated_data' not in st.session_state:
    st.session_state['generated_data'] = None
if 'show_feedback' not in st.session_state:
    st.session_state['show_feedback'] = False
if 'feedback_submitted' not in st.session_state:
    st.session_state['feedback_submitted'] = False

# --- WIDGETS ---
# Centered Card Container for Inputs
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.container(border=True):
        # Single Row: Uploader + Button
        # Adjust column ratios to make button sit nicely next to uploader
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
            process_generation(uploaded_file, status_container=status_container)

# --- DISPLAY RESULTS ---
data = st.session_state.get('generated_data')
if data:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    
    # 1. Summary Cards
    st.markdown("### 📌 Key Concepts")
    summary_points = data.get("summary_points", [])
    
    # Display in a grid of cards
    for i in range(0, len(summary_points), 2):
        cols = st.columns(2)
        # Card 1
        with cols[0]:
            st.markdown(f"""
            <div class="summary-card">
                <span class="summary-number">#{i+1}</span>
                {summary_points[i]}
            </div>
            """, unsafe_allow_html=True)
        
        # Card 2 (if exists)
        if i + 1 < len(summary_points):
            with cols[1]:
                st.markdown(f"""
                <div class="summary-card">
                    <span class="summary-number">#{i+2}</span>
                    {summary_points[i+1]}
                </div>
                """, unsafe_allow_html=True)
    
    # 2. Flashcards
    st.markdown("---")
    st.markdown("### 🗂️ Flashcards")
    flashcards = data.get("flashcards", [])
    
    # Display in a grid of cards (2 columns)
    for i in range(0, len(flashcards), 2):
        cols = st.columns(2)
        
        # Card 1
        with cols[0]:
            with st.container(border=True):
                st.markdown(f"**Q: {flashcards[i]['question']}**")
                with st.expander("Reveal Answer"):
                    st.write(flashcards[i]['answer'])
        
        # Card 2 (if exists)
        if i + 1 < len(flashcards):
            with cols[1]:
                with st.container(border=True):
                    st.markdown(f"**Q: {flashcards[i+1]['question']}**")
                    with st.expander("Reveal Answer"):
                        st.write(flashcards[i+1]['answer'])
    
    # 3. Quiz
    st.markdown("---")
    st.markdown("### 📝 Self-Test")
    
    quiz_data = data.get("quiz", [])
    for i, q in enumerate(quiz_data):
        # Card-based layout for each question
        with st.container(border=True):
            st.markdown(f"#### {i+1}. {q['question']}")
            st.markdown("<br>", unsafe_allow_html=True) # Vertical spacing
            
            # Unique key for each radio button to track state
            user_answer = st.radio(
                "Choose one:", 
                q['options'], 
                key=f"quiz_q_{i}", 
                index=None, 
                label_visibility="collapsed"
            )
            
            # Immediate feedback
            if user_answer:
                # Check if the selected option starts with the correct letter (e.g., "A")
                if user_answer.startswith(q['correct_answer']):
                    st.success(f"✅ Correct! The answer is **{user_answer}**.")
                else:
                    # Find the full text of the correct answer
                    correct_option_text = next((opt for opt in q['options'] if opt.startswith(q['correct_answer'])), q['correct_answer'])
                    st.error(f"❌ Incorrect. The correct answer is **{correct_option_text}**.")
        
        # Margin between cards
        st.markdown("<br>", unsafe_allow_html=True)

# --- FEEDBACK SECTION ---
# Only render if feedback is active
if st.session_state.get('show_feedback'):
    
    # Case 1: Feedback already submitted -> Show Custom Success Message
    if st.session_state.get('feedback_submitted'):
        st.markdown("---")
        
        # Custom HTML Success Box
        st.markdown(
            """
            <div class="success-box">
                <span>Thank you for your feedback!</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Case 2: Feedback NOT submitted -> Show Form
    else:
        st.markdown("---")
        
        # Placeholder for smooth loading/hiding
        feedback_placeholder = st.empty()
        
        with feedback_placeholder.container():
            with st.container(border=True):
                # Header and Close Button
                # Use a very small second column to force right alignment
                col_title, col_close = st.columns([1, 0.05])
                with col_title:
                    st.subheader("⭐ Share Your Feedback")
                with col_close:
                    # Use standard '✕' (Multiplication X) for this button
                    if st.button("✕", key="close_feedback"):
                        st.session_state['show_feedback'] = False
                        st.rerun()
                
                # Feedback Form
                with st.form("feedback_form"):
                    rating_options = ['5 stars ⭐⭐⭐⭐⭐', '4 stars ⭐⭐⭐⭐', '3 stars ⭐⭐⭐', '2 stars ⭐⭐', '1 star ⭐']
                    rating_selection = st.selectbox("Rate your experience", options=rating_options)
                    
                    comment = st.text_area("Additional comments (optional):", height=100)
                    
                    # Standard submit button (no icon styling)
                    submitted = st.form_submit_button("Submit Feedback", type="primary")
                    
                    if submitted:
                        # Extract numeric rating
                        rating_value = int(rating_selection.split(" ")[0])
                        
                        # Hide the form immediately by clearing the placeholder
                        feedback_placeholder.empty()
                        
                        # Show spinner in the now-empty placeholder
                        with feedback_placeholder.container():
                            with st.spinner("Saving your feedback..."):
                                success = submit_feedback(rating_value, comment)
                        
                        if success:
                            st.session_state['feedback_submitted'] = True
                            st.rerun()