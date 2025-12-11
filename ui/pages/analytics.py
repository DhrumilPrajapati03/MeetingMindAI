# ui/pages/3_📈_Analytics.py
"""
Analytics Page
==============
Visualize meeting analytics and trends
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Meeting Analytics")
st.markdown("Insights and trends from your meetings.")

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

# Fetch all meetings
try:
    response = requests.get(f"{API_URL}/api/v1/meetings", params={"skip": 0, "limit": 1000}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        meetings = data.get('meetings', [])
        
        if not meetings:
            st.info("📭 No meetings yet. Upload some meetings to see analytics!")
            st.stop()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(meetings)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['duration_minutes'] = df['duration_seconds'] / 60
        
        # Overview metrics
        st.markdown("### 📊 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_meetings = len(df)
            st.metric("Total Meetings", total_meetings)
        
        with col2:
            total_duration = df['duration_seconds'].sum() / 3600  # hours
            st.metric("Total Hours", f"{total_duration:.1f}h")
        
        with col3:
            completed = len(df[df['status'] == 'completed'])
            st.metric("Completed", f"{completed} ({completed/total_meetings*100:.0f}%)")
        
        with col4:
            avg_duration = df['duration_minutes'].mean()
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
        
        st.markdown("---")
        
        # Time series - Meetings over time
        st.markdown("### 📅 Meeting Frequency Over Time")
        
        df['date'] = df['created_at'].dt.date
        meetings_per_day = df.groupby('date').size().reset_index(name='count')
        
        fig_timeline = px.line(
            meetings_per_day,
            x='date',
            y='count',
            title='Meetings Per Day',
            labels={'date': 'Date', 'count': 'Number of Meetings'}
        )
        fig_timeline.update_traces(line_color='#667eea')
        fig_timeline.update_layout(hovermode='x unified')
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.markdown("---")
        
        # Duration analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⏱️ Meeting Duration Distribution")
            
            fig_duration = px.histogram(
                df[df['duration_minutes'] > 0],
                x='duration_minutes',
                nbins=20,
                title='Distribution of Meeting Durations',
                labels={'duration_minutes': 'Duration (minutes)', 'count': 'Number of Meetings'}
            )
            fig_duration.update_traces(marker_color='#4CAF50')
            
            st.plotly_chart(fig_duration, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Status Breakdown")
            
            status_counts = df['status'].value_counts()
            
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='Meeting Status Distribution',
                color_discrete_map={
                    'completed': '#4CAF50',
                    'processing': '#FFC107',
                    'failed': '#F44336',
                    'uploading': '#2196F3'
                }
            )
            
            st.plotly_chart(fig_status, use_container_width=True)
        
        st.markdown("---")
        
        # Topics analysis
        st.markdown("### 🏷️ Most Common Topics")
        
        # Extract all topics
        all_topics = []
        for topics in df['key_topics'].dropna():
            if isinstance(topics, list):
                all_topics.extend(topics)
        
        if all_topics:
            topic_counts = Counter(all_topics).most_common(15)
            topic_df = pd.DataFrame(topic_counts, columns=['Topic', 'Count'])
            
            fig_topics = px.bar(
                topic_df,
                x='Count',
                y='Topic',
                orientation='h',
                title='Top 15 Discussion Topics',
                color='Count',
                color_continuous_scale='Viridis'
            )
            fig_topics.update_layout(showlegend=False, height=500)
            
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.info("No topic data available yet.")
        
        st.markdown("---")
        
        # Sentiment analysis
        if 'sentiment_score' in df.columns and df['sentiment_score'].notna().any():
            st.markdown("### 😊 Sentiment Trends")
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_sentiment = df['sentiment_score'].mean()
                
                # Gauge chart for average sentiment
                fig_sentiment_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_sentiment,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Average Sentiment"},
                    delta={'reference': 0},
                    gauge={
                        'axis': {'range': [-1, 1]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [-1, -0.3], 'color': "#ffcccc"},
                            {'range': [-0.3, 0.3], 'color': "#ffffcc"},
                            {'range': [0.3, 1], 'color': "#ccffcc"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 0
                        }
                    }
                ))
                
                st.plotly_chart(fig_sentiment_gauge, use_container_width=True)
            
            with col2:
                # Sentiment over time
                sentiment_time = df[df['sentiment_score'].notna()].copy()
                sentiment_time = sentiment_time.sort_values('created_at')
                
                fig_sentiment_time = px.scatter(
                    sentiment_time,
                    x='created_at',
                    y='sentiment_score',
                    title='Sentiment Over Time',
                    labels={'created_at': 'Date', 'sentiment_score': 'Sentiment Score'},
                    color='sentiment_score',
                    color_continuous_scale='RdYlGn',
                    hover_data=['title']
                )
                fig_sentiment_time.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_sentiment_time.update_layout(height=400)
                
                st.plotly_chart(fig_sentiment_time, use_container_width=True)
        
        st.markdown("---")
        
        # Action items analysis
        st.markdown("### 💼 Action Items Overview")
        
        # Count action items per meeting
        action_item_counts = []
        for meeting in meetings:
            if meeting.get('action_items'):
                action_item_counts.append(len(meeting['action_items']))
            else:
                action_item_counts.append(0)
        
        df['action_item_count'] = action_item_counts
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_action_items = df['action_item_count'].sum()
            st.metric("Total Action Items", int(total_action_items))
        
        with col2:
            avg_action_items = df['action_item_count'].mean()
            st.metric("Avg per Meeting", f"{avg_action_items:.1f}")
        
        with col3:
            meetings_with_actions = len(df[df['action_item_count'] > 0])
            st.metric("Meetings with Actions", f"{meetings_with_actions} ({meetings_with_actions/len(df)*100:.0f}%)")
        
        # Action items distribution
        fig_actions = px.histogram(
            df,
            x='action_item_count',
            title='Action Items per Meeting',
            labels={'action_item_count': 'Number of Action Items', 'count': 'Number of Meetings'},
            nbins=15
        )
        fig_actions.update_traces(marker_color='#764ba2')
        
        st.plotly_chart(fig_actions, use_container_width=True)
        
        st.markdown("---")
        
        # Processing efficiency
        st.markdown("### ⚡ Processing Efficiency")
        
        processing_data = df[df['processing_time_seconds'].notna() & df['duration_seconds'].notna()].copy()
        
        if not processing_data.empty:
            processing_data['efficiency_ratio'] = processing_data['processing_time_seconds'] / processing_data['duration_seconds']
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_processing_time = processing_data['processing_time_seconds'].mean()
                st.metric("Avg Processing Time", f"{avg_processing_time:.1f}s")
                
                avg_ratio = processing_data['efficiency_ratio'].mean()
                st.metric("Avg Speed", f"{avg_ratio:.2f}x realtime")
                
                st.caption("Lower is better (e.g., 0.5x = processes 2x faster than realtime)")
            
            with col2:
                fig_efficiency = px.scatter(
                    processing_data,
                    x='duration_minutes',
                    y='processing_time_seconds',
                    title='Processing Time vs Meeting Duration',
                    labels={
                        'duration_minutes': 'Meeting Duration (minutes)',
                        'processing_time_seconds': 'Processing Time (seconds)'
                    },
                    hover_data=['title'],
                    trendline="ols"
                )
                fig_efficiency.update_traces(marker=dict(size=10, opacity=0.6))
                
                st.plotly_chart(fig_efficiency, use_container_width=True)
        
        st.markdown("---")
        
        # Participant analysis
        st.markdown("### 👥 Participant Analysis")
        
        all_participants = []
        for participants in df['participants'].dropna():
            if isinstance(participants, list):
                all_participants.extend(participants)
        
        if all_participants:
            participant_counts = Counter(all_participants).most_common(10)
            participant_df = pd.DataFrame(participant_counts, columns=['Participant', 'Meetings'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Most Active Participants:**")
                st.dataframe(
                    participant_df,
                    hide_index=True,
                    use_container_width=True
                )
            
            with col2:
                fig_participants = px.bar(
                    participant_df,
                    x='Participant',
                    y='Meetings',
                    title='Top Participants by Meeting Count',
                    color='Meetings',
                    color_continuous_scale='Blues'
                )
                fig_participants.update_layout(showlegend=False)
                
                st.plotly_chart(fig_participants, use_container_width=True)
        else:
            st.info("No participant data available.")
        
        st.markdown("---")
        
        # Export data
        st.markdown("### 📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "📊 Download CSV",
                csv,
                "meeting_analytics.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            # Create summary report
            summary_report = f"""
MEETING ANALYTICS SUMMARY
=========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

OVERVIEW:
- Total Meetings: {len(df)}
- Completed: {len(df[df['status'] == 'completed'])}
- Total Duration: {df['duration_seconds'].sum() / 3600:.2f} hours
- Average Duration: {df['duration_minutes'].mean():.1f} minutes

ACTION ITEMS:
- Total: {int(df['action_item_count'].sum())}
- Average per Meeting: {df['action_item_count'].mean():.1f}

SENTIMENT:
- Average Score: {df['sentiment_score'].mean():.2f} (on scale of -1 to 1)

TOP TOPICS:
{chr(10).join([f"- {topic}: {count}" for topic, count in topic_counts[:10]])}
"""
            
            st.download_button(
                "📄 Download Report",
                summary_report,
                "meeting_report.txt",
                "text/plain",
                use_container_width=True
            )
    
    else:
        st.error(f"Failed to fetch meetings: {response.status_code}")

except requests.exceptions.Timeout:
    st.error("Request timeout. Please try again.")
except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

# Sidebar tips
with st.sidebar:
    st.markdown("### 💡 Analytics Tips")
    st.markdown("""
    **Understanding Metrics:**
    
    - **Sentiment Score**: -1 (negative) to 1 (positive)
    - **Processing Speed**: How fast the AI processes vs audio length
    - **RTF (Real-Time Factor)**: <1 is faster than realtime
    
    **Best Practices:**
    - Track trends over time
    - Monitor action item completion
    - Compare meeting efficiency
    - Identify common topics
    """)