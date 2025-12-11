# ui/pages/2_📊_Dashboard.py
"""
Dashboard Page
==============
View all meetings and their details
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Meeting Dashboard")
st.markdown("View and manage all your meetings.")

API_URL = "http://localhost:8000"

# Check API
try:
    health_response = requests.get(f"{API_URL}/health", timeout=2)
    api_online = health_response.status_code == 200
except:
    api_online = False

if not api_online:
    st.error("⚠️ **API is offline!**")
    st.stop()

# Filters
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input("🔍 Search meetings", placeholder="Search by title or description...")

with col2:
    status_filter = st.selectbox(
        "Status",
        ["All", "Completed", "Processing", "Failed"]
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        ["Newest First", "Oldest First", "Title A-Z"]
    )

# Fetch meetings
try:
    params = {"skip": 0, "limit": 100}
    
    if status_filter != "All":
        params["status"] = status_filter.lower()
    
    response = requests.get(f"{API_URL}/api/v1/meetings", params=params, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        meetings = data.get('meetings', [])
        total = data.get('total', 0)
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Meetings", total)
        
        completed = len([m for m in meetings if m['status'] == 'completed'])
        col2.metric("Completed", completed)
        
        processing = len([m for m in meetings if m['status'] == 'processing'])
        col3.metric("Processing", processing)
        
        if meetings:
            avg_duration = sum([m.get('duration_seconds', 0) for m in meetings if m.get('duration_seconds')]) / len(meetings)
            col4.metric("Avg Duration", f"{avg_duration/60:.1f} min")
        
        st.markdown("---")
        
        # Display meetings
        if not meetings:
            st.info("📭 No meetings found. Upload your first meeting to get started!")
        else:
            # Apply search filter
            if search_query:
                meetings = [m for m in meetings if 
                           search_query.lower() in m['title'].lower() or 
                           (m.get('description') and search_query.lower() in m['description'].lower())]
            
            # Apply sorting
            if sort_by == "Oldest First":
                meetings = sorted(meetings, key=lambda x: x['created_at'])
            elif sort_by == "Title A-Z":
                meetings = sorted(meetings, key=lambda x: x['title'])
            else:  # Newest First (default)
                meetings = sorted(meetings, key=lambda x: x['created_at'], reverse=True)
            
            # Display each meeting as a card
            for meeting in meetings:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Title and status
                        status_emoji = {
                            'completed': '✅',
                            'processing': '🔄',
                            'failed': '❌',
                            'uploading': '📤'
                        }.get(meeting['status'], '❓')
                        
                        st.markdown(f"### {status_emoji} {meeting['title']}")
                        
                        if meeting.get('description'):
                            st.markdown(f"*{meeting['description']}*")
                        
                        # Metadata
                        meta_col1, meta_col2, meta_col3 = st.columns(3)
                        
                        with meta_col1:
                            created_date = datetime.fromisoformat(meeting['created_at'].replace('Z', '+00:00'))
                            st.caption(f"📅 {created_date.strftime('%Y-%m-%d %H:%M')}")
                        
                        with meta_col2:
                            if meeting.get('duration_seconds'):
                                duration_min = meeting['duration_seconds'] / 60
                                st.caption(f"⏱️ {duration_min:.1f} min")
                        
                        with meta_col3:
                            if meeting.get('participants'):
                                participants = meeting['participants']
                                if isinstance(participants, list):
                                    st.caption(f"👥 {', '.join(participants[:3])}")
                        
                        # Topics
                        if meeting.get('key_topics'):
                            topics = meeting['key_topics']
                            if isinstance(topics, list):
                                st.markdown("🏷️ " + " • ".join(topics[:5]))
                    
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        if st.button("View Details", key=f"view_{meeting['id']}", use_container_width=True):
                            st.session_state.selected_meeting_id = meeting['id']
                            st.rerun()
                    
                    st.markdown("---")
            
            # Pagination info
            if len(meetings) < total:
                st.info(f"Showing {len(meetings)} of {total} meetings")
    
    else:
        st.error(f"Failed to fetch meetings: {response.status_code}")

except requests.exceptions.Timeout:
    st.error("Request timeout. Please try again.")
except Exception as e:
    st.error(f"Error: {str(e)}")

# Meeting details modal
if 'selected_meeting_id' in st.session_state:
    meeting_id = st.session_state.selected_meeting_id
    
    try:
        response = requests.get(f"{API_URL}/api/v1/meetings/{meeting_id}", timeout=5)
        
        if response.status_code == 200:
            meeting = response.json()
            
            # Show modal-style details
            st.markdown("---")
            st.markdown(f"## 📄 {meeting['title']}")
            
            # Back button
            if st.button("← Back to Dashboard"):
                del st.session_state.selected_meeting_id
                st.rerun()
            
            # Tabs for different sections
            tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcript", "📋 Summary", "💼 Action Items", "📊 Analysis"])
            
            with tab1:
                st.markdown("### Transcript")
                if meeting.get('transcript'):
                    st.text_area("", meeting['transcript'], height=400, disabled=True)
                    
                    # Download button
                    st.download_button(
                        "📥 Download Transcript",
                        meeting['transcript'],
                        file_name=f"{meeting['title']}_transcript.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("Transcript not available yet.")
            
            with tab2:
                st.markdown("### Summary")
                if meeting.get('summary'):
                    st.write(meeting['summary'])
                else:
                    st.info("Summary not available yet.")
            
            with tab3:
                st.markdown("### Action Items")
                action_items = meeting.get('action_items', [])
                
                if action_items:
                    for i, item in enumerate(action_items, 1):
                        with st.expander(f"{i}. {item['title']}", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown(f"**Assigned:** {item.get('assigned_to', 'Unassigned')}")
                            
                            with col2:
                                priority = item.get('priority', 'medium')
                                priority_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
                                st.markdown(f"**Priority:** {priority_emoji.get(priority, '⚪')} {priority.title()}")
                            
                            with col3:
                                due_date = item.get('due_date')
                                st.markdown(f"**Due:** {due_date if due_date else 'Not specified'}")
                            
                            if item.get('description'):
                                st.markdown(f"**Description:** {item['description']}")
                            
                            if item.get('transcript_snippet'):
                                st.caption(f"💬 \"{item['transcript_snippet']}\"")
                else:
                    st.info("No action items found.")
            
            with tab4:
                st.markdown("### Content Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if meeting.get('key_topics'):
                        st.markdown("**🏷️ Key Topics:**")
                        for topic in meeting['key_topics']:
                            st.markdown(f"- {topic}")
                    
                    if meeting.get('sentiment_score') is not None:
                        sentiment = meeting['sentiment_score']
                        st.markdown(f"**😊 Sentiment Score:** {sentiment:.2f}")
                        
                        if sentiment > 0.5:
                            st.success("Overall positive sentiment")
                        elif sentiment < -0.5:
                            st.error("Overall negative sentiment")
                        else:
                            st.info("Neutral sentiment")
                
                with col2:
                    st.markdown("**📊 Metrics:**")
                    if meeting.get('duration_seconds'):
                        st.metric("Duration", f"{meeting['duration_seconds']/60:.1f} min")
                    
                    if meeting.get('word_count'):
                        st.metric("Word Count", meeting['word_count'])
                    
                    if meeting.get('processing_time_seconds'):
                        st.metric("Processing Time", f"{meeting['processing_time_seconds']:.1f}s")
    
    except Exception as e:
        st.error(f"Error loading meeting details: {str(e)}")
        if st.button("← Back"):
            del st.session_state.selected_meeting_id
            st.rerun()