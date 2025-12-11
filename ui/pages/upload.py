# ui/pages/1_📤_Upload.py
"""
Upload Page
===========
Upload audio files for processing
"""

import streamlit as st
import requests
import time
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Upload Meeting", page_icon="📤", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .upload-zone {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 3rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 2rem 0;
    }
    
    .processing-animation {
        text-align: center;
        padding: 2rem;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📤 Upload Meeting")
st.markdown("Upload your meeting audio file for AI-powered transcription and analysis.")

# Check API connection
API_URL = "http://localhost:8000"

try:
    health_response = requests.get(f"{API_URL}/health", timeout=2)
    api_online = health_response.status_code == 200
except:
    api_online = False

if not api_online:
    st.error("⚠️ **API is offline!** Please start the FastAPI server.")
    st.code("python src/main.py", language="bash")
    st.stop()

# Upload form
with st.form("upload_form"):
    st.markdown("### 📁 Meeting Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input(
            "Meeting Title *",
            placeholder="e.g., Q4 Planning Meeting",
            help="Give your meeting a descriptive title"
        )
        
        description = st.text_area(
            "Description (optional)",
            placeholder="e.g., Quarterly planning and budget review",
            help="Add context about the meeting"
        )
    
    with col2:
        participants = st.text_input(
            "Participants (optional)",
            placeholder="e.g., Alice, Bob, Charlie",
            help="Comma-separated list of participant names"
        )
        
        meeting_date = st.date_input(
            "Meeting Date",
            value=datetime.now(),
            help="When did this meeting occur?"
        )
    
    st.markdown("### 🎙️ Audio File")
    
    audio_file = st.file_uploader(
        "Upload audio file",
        type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
        help="Supported formats: WAV, MP3, M4A, FLAC, OGG (Max 500MB)"
    )
    
    # Show file info
    if audio_file:
        file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Filename", audio_file.name)
        col2.metric("Size", f"{file_size_mb:.2f} MB")
        col3.metric("Type", audio_file.type)
        
        if file_size_mb > 500:
            st.error("❌ File too large! Maximum size is 500MB.")
        
        # Estimated processing time
        estimated_duration = file_size_mb * 10  # Rough estimate: 10 seconds per MB
        estimated_processing = estimated_duration * 0.25  # 25% of duration
        st.info(f"⏱️ Estimated processing time: ~{estimated_processing:.0f} seconds")
    
    submitted = st.form_submit_button("🚀 Upload and Process", type="primary", use_container_width=True)

# Process upload
if submitted:
    if not title:
        st.error("❌ Please provide a meeting title.")
    elif not audio_file:
        st.error("❌ Please upload an audio file.")
    else:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Upload file
            status_text.text("📤 Uploading file...")
            progress_bar.progress(20)
            
            files = {
                'file': (audio_file.name, audio_file.getvalue(), audio_file.type)
            }
            
            data = {
                'title': title,
                'description': description if description else '',
                'participants': participants if participants else ''
            }
            
            response = requests.post(
                f"{API_URL}/api/v1/upload",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"❌ Upload failed: {response.text}")
                st.stop()
            
            result = response.json()
            meeting_id = result['meeting_id']
            
            progress_bar.progress(40)
            status_text.text("✅ File uploaded! Processing started...")
            
            # Step 2: Poll for status
            max_wait = 600  # 10 minutes max
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(
                    f"{API_URL}/api/v1/meetings/{meeting_id}/status",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data['status']
                    progress = status_data['progress']
                    
                    progress_bar.progress(min(40 + int(progress * 0.6), 100))
                    
                    if current_status == 'completed':
                        status_text.text("✅ Processing complete!")
                        progress_bar.progress(100)
                        break
                    elif current_status == 'failed':
                        st.error("❌ Processing failed. Please try again.")
                        st.stop()
                    else:
                        status_text.text(f"🔄 Processing... ({progress}%)")
                
                time.sleep(2)  # Poll every 2 seconds
            
            # Step 3: Show success
            st.balloons()
            
            st.markdown("""
            <div class="success-box">
                <h3>✅ Meeting Processed Successfully!</h3>
                <p>Your meeting has been transcribed and analyzed.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Meeting ID", meeting_id)
                st.metric("Status", "✅ Completed")
            
            with col2:
                if st.button("📊 View Meeting Details", type="primary", use_container_width=True):
                    st.switch_page("pages/2_📊_Dashboard.py")
            
            # Show quick preview
            with st.expander("👀 Quick Preview", expanded=True):
                meeting_response = requests.get(f"{API_URL}/api/v1/meetings/{meeting_id}")
                
                if meeting_response.status_code == 200:
                    meeting_data = meeting_response.json()
                    
                    st.markdown("**📝 Transcript Preview:**")
                    transcript = meeting_data.get('transcript', '')
                    st.text(transcript[:500] + "..." if len(transcript) > 500 else transcript)
                    
                    st.markdown("**📋 Summary:**")
                    st.write(meeting_data.get('summary', 'No summary available'))
                    
                    if meeting_data.get('key_topics'):
                        st.markdown("**🔍 Topics:**")
                        st.write(", ".join(meeting_data['key_topics']))
        
        except requests.exceptions.Timeout:
            st.error("❌ Request timeout. The server might be busy.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Sidebar info
with st.sidebar:
    st.markdown("### 📋 Upload Guide")
    st.markdown("""
    **Supported Formats:**
    - WAV (recommended)
    - MP3
    - M4A
    - FLAC
    - OGG
    
    **File Requirements:**
    - Max size: 500MB
    - Max duration: 3 hours
    - Min duration: 1 second
    
    **Tips:**
    - Use clear audio
    - Minimize background noise
    - Single speaker works best
    """)