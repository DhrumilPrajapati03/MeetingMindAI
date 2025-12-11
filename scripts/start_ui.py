# scripts/start_ui.py
"""Start Streamlit UI"""

import sys
from pathlib import Path
import subprocess

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("=" * 60)
    print("Starting MeetingMind AI UI")
    print("=" * 60)
    print()
    print("Access the app at: http://localhost:8501")
    print()
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(project_root / "ui" / "app.py"),
        "--server.port=8501",
        "--server.address=localhost"
    ])