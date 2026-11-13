#!/usr/bin/env python3
"""
VeritasAI Unified Development Launcher
======================================
Automates:
1. Virtual environment creation & verification (backend/venv)
2. Dependency installation (if not already installed)
3. Frontend package check (node_modules)
4. Concurrent launch of FastAPI backend and Vite frontend
5. Graceful shutdown on Ctrl+C (cleans up process trees on Windows/Linux/macOS)
"""

import sys
import os
import shutil
import subprocess
import hashlib
import threading
import signal
import time
import socket
from pathlib import Path

# Enable VT100 / ANSI escape sequences on Windows console
if sys.platform == "win32":
    os.system("")

# ANSI Color codes for clean terminal output
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}", flush=True)

def log_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}", flush=True)

def log_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}", flush=True)

def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}", flush=True)

def log_step(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}==> {title}{Colors.RESET}", flush=True)

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
REQ_FILE = BACKEND_DIR / "requirements.txt"
VENV_DIR = BACKEND_DIR / "venv"

# Platform-specific paths
if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    NPM_CMD = shutil.which("npm.cmd") or shutil.which("npm") or "npm"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    NPM_CMD = shutil.which("npm") or "npm"

HASH_MARKER_FILE = VENV_DIR / ".requirements_installed.sha256"

# Print lock for clean multiplexed console streaming
print_lock = threading.Lock()

def calculate_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_venv_healthy() -> bool:
    """Check if the virtual environment python exists and can execute code."""
    if not VENV_PYTHON.is_file():
        return False
    try:
        res = subprocess.run(
            [str(VENV_PYTHON), "-c", "import sys; sys.exit(0)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return res.returncode == 0
    except Exception:
        return False

def ensure_virtual_environment():
    """Ensure the Python virtual environment exists and is healthy."""
    log_step("1. Checking Virtual Environment")

    if VENV_DIR.exists():
        if is_venv_healthy():
            log_success(f"Virtual environment is active and healthy: {VENV_DIR}")
            return
        else:
            log_warn(f"Existing virtual environment at '{VENV_DIR}' is invalid or from a different machine. Recreating...")
            try:
                shutil.rmtree(VENV_DIR)
            except Exception as e:
                log_warn(f"Failed to cleanly remove old venv directory ({e}). Attempting to overwrite.")

    log_info(f"Creating Python virtual environment at {VENV_DIR}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True
        )
        log_success("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to create virtual environment: {e}")
        sys.exit(1)

def are_backend_packages_installed() -> bool:
    """Determine if required Python packages are already installed."""
    if not REQ_FILE.is_file():
        return True

    current_hash = calculate_file_hash(REQ_FILE)
    if HASH_MARKER_FILE.is_file():
        try:
            saved_hash = HASH_MARKER_FILE.read_text(encoding="utf-8").strip()
            if saved_hash == current_hash:
                return True
        except Exception:
            pass

    # Fallback check: if hash marker doesn't exist yet, test if packages are already installed
    check_script = "import fastapi, uvicorn, slowapi, dotenv, pydantic; sys.exit(0)"
    try:
        res = subprocess.run(
            [str(VENV_PYTHON), "-c", check_script],
            capture_output=True,
            timeout=10
        )
        if res.returncode == 0:
            # Core packages are installed! Write the marker so future runs are instant.
            try:
                HASH_MARKER_FILE.write_text(current_hash, encoding="utf-8")
            except Exception:
                pass
            return True
    except Exception:
        pass

    return False

def install_backend_packages(force: bool = False):
    """Install requirements if not already satisfied."""
    log_step("2. Checking Backend Python Packages")

    if not REQ_FILE.is_file():
        log_warn(f"requirements.txt not found at {REQ_FILE}. Skipping backend installation.")
        return

    if not force and are_backend_packages_installed():
        log_success("Backend packages are already installed and verified. Skipping pip install.")
        return

    log_info("Installing backend packages from backend/requirements.txt...")
    start_time = time.time()
    try:
        # Run pip install using the venv python
        cmd = [str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQ_FILE)]
        subprocess.run(cmd, check=True)

        # Mark hash upon successful installation
        current_hash = calculate_file_hash(REQ_FILE)
        HASH_MARKER_FILE.write_text(current_hash, encoding="utf-8")
        elapsed = time.time() - start_time
        log_success(f"Backend packages installed successfully in {elapsed:.1f}s.")
    except subprocess.CalledProcessError as e:
        log_error(f"pip install failed with exit code {e.returncode}.")
        sys.exit(1)

def check_frontend_packages():
    """Ensure frontend dependencies exist (node_modules)."""
    log_step("3. Checking Frontend Packages")
    node_modules = ROOT_DIR / "node_modules"

    if node_modules.is_dir():
        log_success("Frontend packages (node_modules) are present. Skipping npm install.")
        return

    log_info("node_modules not found. Running 'npm install'...")
    try:
        subprocess.run([NPM_CMD, "install"], cwd=str(ROOT_DIR), check=True)
        log_success("Frontend packages installed successfully.")
    except subprocess.CalledProcessError as e:
        log_error(f"'npm install' failed with exit code {e.returncode}.")
        sys.exit(1)
    except FileNotFoundError:
        log_error(f"'{NPM_CMD}' executable not found. Make sure Node.js and npm are installed and in your PATH.")
        sys.exit(1)

def check_env_files():
    """Check if necessary environment files exist."""
    backend_env = BACKEND_DIR / ".env"
    root_env = ROOT_DIR / ".env"

    if not backend_env.exists():
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            log_warn(f"backend/.env not found! You can copy it from backend/.env.example")
        else:
            log_warn("backend/.env not found!")

    if not root_env.exists():
        example = ROOT_DIR / ".env.example"
        if example.exists():
            log_warn("Root .env not found! You can copy it from .env.example")

def stream_process_output(pipe, prefix: str, color: str):
    """Read output stream line by line and print with a colored prefix."""
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            stripped = line.rstrip()
            with print_lock:
                print(f"{color}{prefix}{Colors.RESET} {stripped}", flush=True)
    except (ValueError, OSError):
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass

def kill_process_tree(proc: subprocess.Popen):
    """Terminate a process and all of its child processes."""
    if proc is None or proc.poll() is not None:
        return

    pid = proc.pid
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=5
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def main():
    print(f"""
{Colors.CYAN}{Colors.BOLD}============================================================
              VeritasAI Development Launcher                
============================================================{Colors.RESET}
Project Root: {ROOT_DIR}
Python:       {sys.version.split()[0]}
Node / npm:   {NPM_CMD}
""")

    # Parse simple arguments
    force_install = "--force-install" in sys.argv or "-f" in sys.argv
    backend_only = "--backend-only" in sys.argv
    frontend_only = "--frontend-only" in sys.argv

    # Step 1: Ensure venv
    ensure_virtual_environment()

    # Step 2: Ensure backend dependencies
    if not frontend_only:
        install_backend_packages(force=force_install)

    # Step 3: Ensure frontend dependencies
    if not backend_only:
        check_frontend_packages()

    # Check env configuration
    check_env_files()

    # Check port conflicts
    if not frontend_only and is_port_in_use(8000):
        log_warn("Port 8000 is already in use. The backend may fail to start or conflict with another running process.")
    if not backend_only and is_port_in_use(5173):
        log_warn("Port 5173 is already in use. Vite will automatically pick the next available port (e.g. 5174).")

    log_step("4. Starting Servers")

    processes = []
    threads = []

    # Prepare backend environment
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"

    backend_proc = None
    frontend_proc = None

    try:
        # Start Backend
        if not frontend_only:
            log_info(f"Starting Backend API on http://localhost:8000 (Docs: http://localhost:8000/docs)...")
            backend_cmd = [
                str(VENV_PYTHON),
                "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            backend_proc = subprocess.Popen(
                backend_cmd,
                cwd=str(BACKEND_DIR),
                env=backend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                preexec_fn=None if sys.platform == "win32" else os.setsid
            )
            processes.append(backend_proc)

            t_backend = threading.Thread(
                target=stream_process_output,
                args=(backend_proc.stdout, "[BACKEND]", Colors.CYAN),
                daemon=True
            )
            t_backend.start()
            threads.append(t_backend)

        # Start Frontend
        if not backend_only:
            log_info(f"Starting Frontend Vite Dev Server on http://localhost:5173...")
            frontend_cmd = [NPM_CMD, "run", "dev"]
            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                preexec_fn=None if sys.platform == "win32" else os.setsid
            )
            processes.append(frontend_proc)

            t_frontend = threading.Thread(
                target=stream_process_output,
                args=(frontend_proc.stdout, "[FRONTEND]", Colors.GREEN),
                daemon=True
            )
            t_frontend.start()
            threads.append(t_frontend)

        print(f"\n{Colors.BOLD}{Colors.GREEN}============================================================{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}  Both services are running! Press Ctrl+C to stop all servers{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}============================================================{Colors.RESET}\n")

        # Monitor processes
        while True:
            for p in processes:
                exit_code = p.poll()
                if exit_code is not None:
                    name = "Backend" if p == backend_proc else "Frontend"
                    log_warn(f"{name} exited unexpectedly with code {exit_code}.")
                    raise KeyboardInterrupt
            time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[SHUTDOWN] Stopping all servers...{Colors.RESET}")
    finally:
        for p in processes:
            kill_process_tree(p)
        log_success("All servers stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
