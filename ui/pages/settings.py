# ui/pages/4_⚙️_Settings.py
"""
Settings Page
=============
Configuration and system settings
"""

import streamlit as st
import requests
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")
st.markdown("Configure your MeetingMind AI application.")

API_URL = "http://localhost:8000"

# Check API
try:
    health_response = requests.get(f"{API_URL}/health", timeout=2)
    api_online = health_response.status_code == 200
    health_data = health_response.json() if api_online else {}
except:
    api_online = False
    health_data = {}

# System Status
st.markdown("### 🔌 System Status")

col1, col2, col3 = st.columns(3)

with col1:
    if api_online:
        st.success("✅ FastAPI")
    else:
        st.error("❌ FastAPI")

with col2:
    db_status = health_data.get('services', {}).get('database', 'unknown')
    if db_status == 'healthy':
        st.success("✅ Database")
    else:
        st.error("❌ Database")

with col3:
    storage_status = health_data.get('services', {}).get('storage', 'unknown')
    if storage_status == 'healthy':
        st.success("✅ Storage")
    else:
        st.error("❌ Storage")

st.markdown("---")

# API Information
st.markdown("### 📡 API Configuration")

col1, col2 = st.columns(2)

with col1:
    st.text_input("API Base URL", value=API_URL, disabled=True)

with col2:
    if api_online:
        try:
            info_response = requests.get(f"{API_URL}/info", timeout=2)
            if info_response.status_code == 200:
                info_data = info_response.json()
                st.text_input("API Version", value=info_data.get('version', 'Unknown'), disabled=True)
        except:
            pass

# View supported formats
if st.button("📋 View Supported Audio Formats"):
    try:
        formats_response = requests.get(f"{API_URL}/api/v1/upload/formats", timeout=2)
        if formats_response.status_code == 200:
            formats_data = formats_response.json()
            
            st.markdown("**Supported Formats:**")
            st.write(", ".join(formats_data.get('supported_formats', [])))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Max File Size", f"{formats_data.get('max_file_size_mb', 0)} MB")
            with col2:
                st.metric("Max Duration", f"{formats_data.get('max_duration_hours', 0)} hours")
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("---")

# Service URLs
st.markdown("### 🔗 Service URLs")

services = {
    "FastAPI": "http://localhost:8000",
    "API Documentation": "http://localhost:8000/docs",
    "Prometheus": "http://localhost:9090",
    "Grafana": "http://localhost:3000",
    "MinIO Console": "http://localhost:9001",
    "Qdrant Dashboard": "http://localhost:6333/dashboard"
}

cols = st.columns(2)

for i, (service, url) in enumerate(services.items()):
    with cols[i % 2]:
        st.markdown(f"**{service}:**")
        st.code(url, language=None)

st.markdown("---")

# Application Info
st.markdown("### ℹ️ Application Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Version:** 1.0.0  
    **Framework:** Streamlit  
    **Backend:** FastAPI  
    **AI Models:** Whisper, Llama 3.3  
    """)

with col2:
    st.markdown("""
    **Features:**
    - 🎙️ Audio transcription
    - 🔍 Content analysis
    - 💼 Action item extraction
    - 📝 Summary generation
    """)

st.markdown("---")

# Data Management
st.markdown("### 🗄️ Data Management")

st.warning("⚠️ **Danger Zone** - These actions cannot be undone!")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Clear Cache", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared!")

with col2:
    if st.button("🔄 Restart Application", type="secondary", use_container_width=True, disabled=True):
        st.info("Manual restart required. Stop and restart the Streamlit app.")

st.markdown("---")

# Troubleshooting
with st.expander("🛠️ Troubleshooting Guide"):
    st.markdown("""
    ### Common Issues
    
    **API is offline:**
```bash
    # Start the FastAPI server
    python src/main.py
```
    
    **Database connection failed:**
```bash
    # Check Docker services
    docker-compose ps
    
    # Restart services
    docker-compose restart postgres
```
    
    **Celery not processing:**
```bash
    # Start Celery worker
    python scripts/start_celery.py
```
    
    **Upload fails:**
    - Check file size (max 500MB)
    - Check file format (WAV, MP3, M4A, etc.)
    - Ensure MinIO is running
    
    **Processing stuck:**
    - Check Celery worker logs
    - Check Groq API key is valid
    - Monitor system resources
    """)

# Logs viewer
with st.expander("📋 System Logs"):
    if st.button("Refresh Logs"):
        try:
            # Try to get recent logs
            log_file = Path("data/logs/app.log")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = f.readlines()[-50:]  # Last 50 lines
                    st.code("".join(logs), language="log")
            else:
                st.info("No log file found.")
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")

st.markdown("---")

# About
st.markdown("### 📚 Resources")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Documentation:**
    - [FastAPI Docs](http://localhost:8000/docs)
    - [Streamlit Docs](https://docs.streamlit.io)
    """)

with col2:
    st.markdown("""
    **Monitoring:**
    - [Prometheus](http://localhost:9090)
    - [Grafana](http://localhost:3000)
    """)

with col3:
    st.markdown("""
    **AI Models:**
    - [Whisper](https://github.com/openai/whisper)
    - [Groq](https://console.groq.com)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>MeetingMind AI</strong> - Transform meetings into actionable insights</p>
    <p><small>Built with ❤️ using FastAPI, Whisper, Groq, and Streamlit</small></p>
</div>
""", unsafe_allow_html=True)