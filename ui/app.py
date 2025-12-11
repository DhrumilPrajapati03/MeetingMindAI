# ui/app.py
"""
MeetingMind AI - Streamlit UI
==============================
Beautiful web interface for meeting intelligence
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/meeting-intelligence',
        'Report a bug': "https://github.com/yourusername/meeting-intelligence/issues",
        'About': "# MeetingMind AI\nAI-powered meeting intelligence platform"
    }
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #4CAF50;
        --secondary-color: #2196F3;
        --background-color: #f5f5f5;
        --text-color: #333333;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Cards */
    .metric-card {
        background: black;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .status-completed {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-processing {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-failed {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
    }
    
    /* Success/error messages */
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎙️ MeetingMind AI")
    st.markdown("---")
    
    # Navigation
    st.markdown("### 📑 Navigation")
    if hasattr(st, "page_link"):
        st.page_link("pages/1_📤_Upload.py", label="📤 Upload Meeting", icon="📤")
        st.page_link("pages/2_📊_Dashboard.py", label="📊 Dashboard", icon="📊")
        st.page_link("pages/3_📈_Analytics.py", label="📈 Analytics", icon="📈")
        st.page_link("pages/4_⚙️_Settings.py", label="⚙️ Settings", icon="⚙️")
        st.page_link("pages/5_🎙️_Live.py", label="🎙️ Live Transcription", icon="🎙️")
    else:
        st.write("Use the sidebar menu to navigate.")
    
    st.markdown("---")
    
    # API Status
    st.markdown("### 🔌 System Status")
    
    # Check API connection
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")
    
    st.markdown("---")
    
    # Quick stats
    try:
        response = requests.get("http://localhost:8000/api/v1/meetings", timeout=2)
        if response.status_code == 200:
            data = response.json()
            st.metric("Total Meetings", data.get('total', 0))
    except:
        pass
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **MeetingMind AI** uses advanced AI to:
    - 🎙️ Transcribe meetings
    - 🔍 Extract insights
    - 💼 Find action items
    - 📝 Generate summaries
    """)

# Main content
st.markdown("""
<div class="main-header">
    <h1>🎙️ MeetingMind AI</h1>
    <p>Transform your meetings into actionable insights with AI</p>
</div>
""", unsafe_allow_html=True)

# Welcome message
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>📤 Upload</h3>
        <p>Upload audio files and let AI transcribe and analyze your meetings.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>🔍 Analyze</h3>
        <p>Extract topics, action items, sentiment, and key decisions automatically.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>📊 Insights</h3>
        <p>Get summaries, track action items, and visualize meeting analytics.</p>
    </div>
    """, unsafe_allow_html=True)

# Quick start guide
st.markdown("---")
st.markdown("### 🚀 Quick Start")

st.markdown("""
1. **Upload a meeting** → Click "📤 Upload Meeting" in the sidebar
2. **Wait for processing** → AI transcribes and analyzes (takes ~1 minute per minute of audio)
3. **View results** → Check dashboard for transcript, summary, and action items
4. **Track progress** → Monitor your meeting analytics over time
""")

# System requirements
with st.expander("💡 Tips for Best Results"):
    st.markdown("""
    **Audio Quality:**
    - Clear audio with minimal background noise
    - Single speaker or well-separated speakers
    - Formats: WAV, MP3, M4A, FLAC
    - Max size: 500MB
    - Max duration: 3 hours
    
    **For Action Items:**
    - Clearly state assignments ("Alice, can you...")
    - Mention deadlines ("by Friday", "next week")
    - Use names of participants
    
    **Processing Time:**
    - Typical: 20-30% of audio duration
    - Example: 10-minute meeting = ~2-3 minutes processing
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Built with ❤️ using FastAPI, Whisper, Groq, and Streamlit</p>
    <p><small>Version 1.0.0 | © 2025 MeetingMind AI</small></p>
</div>
""", unsafe_allow_html=True)