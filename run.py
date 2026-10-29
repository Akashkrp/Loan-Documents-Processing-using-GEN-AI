import subprocess
import sys
import time
import os
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 safely on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

def run_services():
    print("=" * 60)
    print(">> Starting Intelligent Loan Document Processor")
    print("=" * 60)

    # 1. Start FastAPI Backend
    print("\n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    backend_proc = subprocess.Popen(backend_cmd)

    # Give backend a moment to initialize
    time.sleep(3)

    # 2. Start Streamlit Frontend
    print("\n[2/2] Launching Streamlit Frontend on http://localhost:8501 ...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py"
    ]
    frontend_proc = subprocess.Popen(frontend_cmd)

    print("\n" + "=" * 60)
    print(">> System is live!")
    print("   * Backend:  http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)")
    print("   * Frontend: http://localhost:8501")
    print("=" * 60)
    print("\nPress Ctrl+C at any time to stop both services.\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("\n[!] Backend server stopped unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("\n[!] Frontend app stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[*] Received exit signal. Stopping services...")
    finally:
        for name, proc in [("Frontend", frontend_proc), ("Backend", backend_proc)]:
            if proc and proc.poll() is None:
                print(f"Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("Done. Shutdown complete.")

if __name__ == "__main__":
    run_services()
