# ui/pages/5_🎙️_Live.py
"""
Live Transcription Page
========================
Real-time audio transcription with browser microphone access
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Live Transcription", page_icon="🎙️", layout="wide")

st.title("🎙️ Live Transcription")
st.markdown("Real-time audio transcription using WebSocket streaming.")

# Meeting configuration
col1, col2 = st.columns(2)

with col1:
    meeting_title = st.text_input(
        "Meeting Title",
        value=f"Live Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        key="meeting_title"
    )

with col2:
    language = st.selectbox(
        "Language",
        options=["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"],
        index=0,
        key="language"
    )

participants = st.text_input(
    "Participants (comma-separated)",
    placeholder="Alice, Bob, Charlie",
    key="participants"
)

st.markdown("---")

# Embed custom HTML/JS component for audio capture
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 20px;
            margin: 0;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            align-items: center;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .btn-start {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn-start:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-stop {{
            background-color: #dc3545;
            color: white;
        }}
        
        .btn-stop:hover {{
            background-color: #c82333;
        }}
        
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .status {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
        }}
        
        .status-idle {{
            background-color: #f8f9fa;
            color: #6c757d;
        }}
        
        .status-recording {{
            background-color: #fff5f5;
            color: #dc3545;
        }}
        
        .status-connecting {{
            background-color: #fff9e6;
            color: #ff9800;
        }}
        
        .recording-dot {{
            width: 12px;
            height: 12px;
            background-color: #dc3545;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.5; transform: scale(1.1); }}
        }}
        
        .transcript-box {{
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            min-height: 400px;
            max-height: 600px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .transcript-box.empty {{
            color: #adb5bd;
            font-style: italic;
        }}
        
        .transcript-entry {{
            margin-bottom: 15px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        
        .transcript-time {{
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
        }}
        
        .transcript-text {{
            color: #212529;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            flex: 1;
            padding: 15px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #212529;
        }}
        
        .error-message {{
            padding: 15px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            color: #721c24;
            margin-bottom: 20px;
        }}
        
        .info-message {{
            padding: 15px;
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            color: #0c5460;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Controls -->
        <div class="controls">
            <button id="startBtn" class="btn btn-start">🎙️ Start Recording</button>
            <button id="stopBtn" class="btn btn-stop" disabled>⏹️ Stop Recording</button>
            <div id="status" class="status status-idle">
                ⚪ Idle
            </div>
        </div>
        
        <!-- Error/Info messages -->
        <div id="messageBox"></div>
        
        <!-- Transcript -->
        <h3>📝 Live Transcript</h3>
        <div id="transcript" class="transcript-box empty">
            Transcript will appear here in real-time...
        </div>
        
        <!-- Statistics -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Duration</div>
                <div class="stat-value" id="duration">0:00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Words</div>
                <div class="stat-value" id="wordCount">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Meeting ID</div>
                <div class="stat-value" id="meetingId">-</div>
            </div>
        </div>
    </div>
    
    <script>
        let websocket = null;
        let mediaRecorder = null;
        let audioContext = null;
        let isRecording = false;
        let startTime = null;
        let durationTimer = null;
        let transcriptText = '';
        let wordCount = 0;
        let sessionId = null;
        let meetingId = null;
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDiv = document.getElementById('status');
        const transcriptDiv = document.getElementById('transcript');
        const messageBox = document.getElementById('messageBox');
        const durationDiv = document.getElementById('duration');
        const wordCountDiv = document.getElementById('wordCount');
        const meetingIdDiv = document.getElementById('meetingId');
        
        // Configuration from Streamlit
        const config = {{
            meetingTitle: "{meeting_title}",
            language: "{language}",
            participants: "{participants}".split(',').map(p => p.trim()).filter(p => p),
            wsUrl: "ws://localhost:8000/api/v1/ws/transcribe"
        }};
        
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        
        async function startRecording() {{
            try {{
                showMessage('Requesting microphone access...', 'info');
                
                // Request microphone access
                const stream = await navigator.mediaDevices.getUserMedia({{
                    audio: {{
                        channelCount: 1,
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true
                    }}
                }});
                
                clearMessage();
                
                // Connect WebSocket
                updateStatus('connecting', '🔄 Connecting...');
                websocket = new WebSocket(config.wsUrl);
                
                websocket.onopen = () => {{
                    console.log('WebSocket connected');
                    
                    // Send start command
                    websocket.send(JSON.stringify({{
                        type: 'start',
                        meeting_title: config.meetingTitle,
                        language: config.language,
                        participants: config.participants
                    }}));
                }};
                
                websocket.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                }};
                
                websocket.onerror = (error) => {{
                    console.error('WebSocket error:', error);
                    showMessage('WebSocket connection error. Is the API running?', 'error');
                    stopRecording();
                }};
                
                websocket.onclose = () => {{
                    console.log('WebSocket closed');
                    if (isRecording) {{
                        stopRecording();
                    }}
                }};
                
                // Setup audio processing
                audioContext = new (window.AudioContext || window.webkitAudioContext)({{
                    sampleRate: 16000
                }});
                
                const source = audioContext.createMediaStreamSource(stream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                processor.onaudioprocess = (e) => {{
                    if (websocket && websocket.readyState === WebSocket.OPEN && isRecording) {{
                        const inputData = e.inputBuffer.getChannelData(0);
                        
                        // Convert Float32Array to Int16Array
                        const pcmData = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {{
                            const s = Math.max(-1, Math.min(1, inputData[i]));
                            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }}
                        
                        // Convert to base64
                        const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(pcmData.buffer)));
                        
                        // Send to server
                        websocket.send(JSON.stringify({{
                            type: 'audio',
                            data: base64Audio
                        }}));
                    }}
                }};
                
                source.connect(processor);
                processor.connect(audioContext.destination);
                
                // Update UI
                isRecording = true;
                startBtn.disabled = true;
                stopBtn.disabled = false;
                updateStatus('recording', '🔴 Recording...');
                
                // Start duration timer
                startTime = Date.now();
                durationTimer = setInterval(updateDuration, 1000);
                
            }} catch (error) {{
                console.error('Error starting recording:', error);
                showMessage('Failed to access microphone. Please grant permission.', 'error');
            }}
        }}
        
        function stopRecording() {{
            if (websocket && websocket.readyState === WebSocket.OPEN) {{
                websocket.send(JSON.stringify({{ type: 'stop' }}));
            }}
            
            if (audioContext) {{
                audioContext.close();
                audioContext = null;
            }}
            
            if (durationTimer) {{
                clearInterval(durationTimer);
            }}
            
            isRecording = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            updateStatus('idle', '⚪ Idle');
        }}
        
        function handleWebSocketMessage(data) {{
            console.log('Received:', data.type, data);
            
            switch (data.type) {{
                case 'connected':
                    console.log('Session connected:', data.session_id);
                    break;
                
                case 'session_started':
                    sessionId = data.session_id;
                    meetingId = data.meeting_id;
                    meetingIdDiv.textContent = meetingId;
                    showMessage('Recording started! Speak into your microphone.', 'info');
                    setTimeout(clearMessage, 3000);
                    break;
                
                case 'transcript':
                    if (data.text && data.text.trim()) {{
                        addTranscriptEntry(data.text, data.timestamp);
                    }}
                    break;
                
                case 'session_ended':
                    showMessage(`Recording saved! Meeting ID: ${{data.meeting_id}}`, 'info');
                    stopRecording();
                    break;
                
                case 'error':
                    showMessage(`Error: ${{data.message}}`, 'error');
                    break;
            }}
        }}
        
        function addTranscriptEntry(text, timestamp) {{
            if (transcriptDiv.classList.contains('empty')) {{
                transcriptDiv.classList.remove('empty');
                transcriptDiv.innerHTML = '';
            }}
            
            const entry = document.createElement('div');
            entry.className = 'transcript-entry';
            
            const time = new Date(timestamp).toLocaleTimeString();
            
            entry.innerHTML = `
                <div class="transcript-time">${{time}}</div>
                <div class="transcript-text">${{text}}</div>
            `;
            
            transcriptDiv.appendChild(entry);
            transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
            
            // Update stats
            transcriptText += ' ' + text;
            wordCount = transcriptText.trim().split(/\s+/).length;
            wordCountDiv.textContent = wordCount;
        }}
        
        function updateDuration() {{
            if (startTime) {{
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                durationDiv.textContent = `${{minutes}}:${{seconds.toString().padStart(2, '0')}}`;
            }}
        }}
        
        function updateStatus(type, text) {{
            statusDiv.className = `status status-${{type}}`;
            
            if (type === 'recording') {{
                statusDiv.innerHTML = '<div class="recording-dot"></div> ' + text;
            }} else {{
                statusDiv.textContent = text;
            }}
        }}
        
        function showMessage(text, type) {{
            const className = type === 'error' ? 'error-message' : 'info-message';
            messageBox.innerHTML = `<div class="${{className}}">${{text}}</div>`;
        }}
        
        function clearMessage() {{
            messageBox.innerHTML = '';
        }}
        
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
            showMessage('Your browser does not support audio recording. Please use Chrome, Firefox, or Edge.', 'error');
            startBtn.disabled = true;
        }}
    </script>
</body>
</html>
"""

# Render the HTML component
components.html(html_code, height=800, scrolling=True)

# Instructions
with st.expander("📖 How to Use Live Transcription"):
    st.markdown("""
    ### Setup:
    1. Make sure your **microphone is connected** and working
    2. Grant **microphone permission** when prompted by browser
    3. Ensure **FastAPI server is running** (port 8000)
    
    ### Recording:
    1. Click **"Start Recording"** button
    2. Wait for "Recording started!" message
    3. **Speak clearly** into your microphone
    4. Transcript will appear in **~3 second chunks**
    5. Click **"Stop Recording"** when done
    
    ### Tips:
    - **Speak clearly** and at normal pace
    - **Minimize background noise** for best results
    - **Stay close** to microphone (but not too close)
    - **Use headphones** to prevent echo/feedback
    - **Stable internet** required for WebSocket
    
    ### Technical Requirements:
    - Modern browser (Chrome, Firefox, Edge, Safari)
    - Microphone access permission
    - WebSocket support (built into all modern browsers)
    - FastAPI server running on localhost:8000
    
    ### Troubleshooting:
    - **"Microphone access denied"**: Check browser permissions
    - **"WebSocket connection error"**: Start FastAPI server
    - **No transcript appearing**: Check microphone is working, try speaking louder
    - **Slow transcription**: Normal - processes every ~3 seconds
    """)

# Sidebar info
with st.sidebar:
    st.markdown("### 🎙️ Live Transcription")
    st.markdown("---")
    
    st.markdown("**Status:**")
    st.info("Check the status indicator in the main area")
    
    st.markdown("---")
    
    st.markdown("**Processing:**")
    st.markdown("""
    - Audio chunks: 1-3 seconds
    - Latency: ~3-5 seconds
    - Model: Whisper base
    - Sample rate: 16kHz
    """)
    
    st.markdown("---")
    
    st.markdown("**After Recording:**")
    st.markdown("""
    1. Meeting auto-saved to database
    2. View in Dashboard
    3. Can run full AI analysis
    4. Extract action items & summary
    """)