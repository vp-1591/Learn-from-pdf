import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import json
import pandas as pd
import os
import re
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
env_api_key = os.getenv("GOOGLE_API_KEY")

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
    /* Target the vertical block wrapper that has a border */
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
        /* Global Background & Text */
        .stApp {
            background-color: #0E1117; /* Streamlit default dark bg */
            color: #FAFAFA;
        }
        
        h1, h2, h3 {
            color: #F0F2F6; /* Light grey for headers */
        }

        /* Hero Section */
        .hero-subtitle {
            color: #BFC5D3; /* Lighter grey for subtitle */
        }

        /* Floating Card Container (Vertical Block) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1F242C;
            border: 1px solid #384455;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); /* Softer, darker shadow */
        }

        /* Summary Cards */
        .summary-card {
            background-color: #1F242C;
            border: 1px solid #384455;
            color: #E0E0E0;
            box-shadow: none; /* Remove shadow or make very subtle */
        }
        .summary-card:hover {
            background-color: #262B33;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .summary-number {
            color: #818CF8; /* Lighter Indigo for dark mode */
        }

        /* Quiz Container */
        .quiz-container {
            background-color: #1F242C;
            border-left: 5px solid #818CF8;
            color: #E0E0E0;
            box-shadow: none;
        }

        /* Flashcards (Streamlit Containers) */
        /* Adjusting standard text colors if needed */
        p, li, span {
            color: #E0E0E0;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- API KEY LOGIC ---
if env_api_key:
    api_key = env_api_key
else:
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# --- HELPER FUNCTIONS ---

def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_youtube_transcript(video_url):
    """
    Optimized for youtube-transcript-api v1.2.3
    Uses Object Access (entry.text) instead of Dictionary Access (entry['text']).
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return None
        
    try:
        # 1. Instantiate the Class
        ytt = YouTubeTranscriptApi()
        
        # 2. Fetch Transcript
        # Tries manual English, then falls back to auto-generated
        transcript = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        
        # 3. Process Text
        text_list = []
        for entry in transcript:
            if hasattr(entry, 'text'):
                text_list.append(entry.text)
            else:
                text_list.append(entry.get('text', ''))
                
        return " ".join(text_list)
        
    except Exception as e:
        print(f"Error: {e}")
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

# --- MAIN APP UI ---

# Hero Section
st.markdown('<div class="hero-title">AutoStudy AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Turn any video or text into flashcards & quizzes in seconds.</div>', unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'study_material' not in st.session_state:
    st.session_state['study_material'] = ""
if 'last_video_url' not in st.session_state:
    st.session_state['last_video_url'] = None
if 'last_study_material' not in st.session_state:
    st.session_state['last_study_material'] = ""
if 'generated_data' not in st.session_state:
    st.session_state['generated_data'] = None

# --- AUTO-FETCH LOGIC (Run before widgets) ---
# Check if video URL has changed
current_video_url = st.session_state.get('video_url')
if current_video_url != st.session_state['last_video_url']:
    if current_video_url:
        with st.spinner("🎧 Listening to video and extracting transcript..."):
            transcript_text = get_youtube_transcript(current_video_url)
            if transcript_text:
                st.session_state['study_material'] = transcript_text
                st.success("Transcript loaded successfully!")
            else:
                st.error("Could not extract text. (Note: This tool requires videos with captions enabled)")
    
    # Update last_video_url to prevent re-fetching
    st.session_state['last_video_url'] = current_video_url

# --- WIDGETS ---
# Centered Card Container for Inputs
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.container(border=True):
        tab1, tab2 = st.tabs(["📚 Text Input", "🎥 YouTube Video"])

        with tab1:
            st.text_area(
                "Paste notes or article text:", 
                height=200, 
                placeholder="Paste your study material here...",
                key="study_material"
            )

        with tab2:
            st.text_input("Paste YouTube URL:", placeholder="https://www.youtube.com/watch?v=...", key="video_url")
            if st.session_state.get("video_url"):
                st.video(st.session_state["video_url"])

# --- AUTO-GENERATE LOGIC ---
# Check if study material has changed (either from transcript fetch or manual edit)
current_study_material = st.session_state.get('study_material')
if current_study_material and current_study_material != st.session_state['last_study_material']:
    if not api_key:
        st.warning("API Key missing. Please enter it in the sidebar.")
    else:
        with st.spinner("✨ Curating your study materials..."):
            data = generate_study_material(current_study_material, api_key)
            if data:
                st.session_state['generated_data'] = data
            
    # Update last_study_material to prevent re-generating
    st.session_state['last_study_material'] = current_study_material

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