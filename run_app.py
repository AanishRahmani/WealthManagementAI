"""
WealthAdvisorAI - Application Launcher
Runs both FastAPI backend and Streamlit frontend concurrently
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

BACKEND_PORT = 8081
FRONTEND_PORT = 8501
BACKEND_HOST = "127.0.0.1"

def run_server():
    print("-" * 60)
    print("  Wealth Advisor AI - Starting Application")
    print("-" * 60)
    
    project_root = Path(__file__).parent.absolute()
    frontend_dir = project_root / "frontend"
    
    print(f"\nStarting FastAPI backend on http://{BACKEND_HOST}:{BACKEND_PORT}")
    backend_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "run_api:app",
            "--host", BACKEND_HOST,
            "--port", str(BACKEND_PORT),
            "--reload",
            "--log-level", "info"
        ],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Waiting for backend to initialize...")
    time.sleep(3)
    
    if backend_process.poll() is not None:
        print("Backend failed to start. Check for errors:")
        if backend_process.stderr:
            print(backend_process.stderr.read())
        sys.exit(1)
    
    print(f"Backend running on http://{BACKEND_HOST}:{BACKEND_PORT}")
    
    print(f"\nStarting Streamlit frontend on http://localhost:{FRONTEND_PORT}")
    frontend_process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit",
            "run", "app.py",
            "--server.port", str(FRONTEND_PORT),
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.serverAddress", f"localhost:{FRONTEND_PORT}",
            "--browser.gatherUsageStats", "false"
        ],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Waiting for frontend to initialize...")
    time.sleep(5)
    
    if frontend_process.poll() is not None:
        print("Frontend failed to start. Check for errors:")
        if frontend_process.stderr:
            print(frontend_process.stderr.read())
        backend_process.terminate()
        sys.exit(1)
    
    print(f"Frontend running on http://localhost:{FRONTEND_PORT}")
    
    print("\n" + "-" * 60)
    print("  Application is ready!")
    print(f"  Dashboard: http://localhost:{FRONTEND_PORT}")
    print(f"  Chat:      http://localhost:{FRONTEND_PORT}/Chat")
    print(f"  API:       http://{BACKEND_HOST}:{BACKEND_PORT}")
    print("-" * 60)
    print("\nPress Ctrl+C to stop all servers")
    
    def signal_handler(sig, frame):
        print("\n\nShutting down servers...")
        
        print("Stopping frontend...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
        
        print("Stopping backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        
        print("All servers stopped.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            time.sleep(1)
            
            if backend_process.poll() is not None:
                print("Backend process died unexpectedly")
                if backend_process.stderr:
                    print(backend_process.stderr.read())
                signal_handler(signal.SIGINT, None)
            
            if frontend_process.poll() is not None:
                print("Frontend process died unexpectedly")
                if frontend_process.stderr:
                    print(frontend_process.stderr.read())
                signal_handler(signal.SIGINT, None)
    
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

def check_dependencies():
    required_packages = ["streamlit", "fastapi", "uvicorn"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    check_dependencies()
    run_server()