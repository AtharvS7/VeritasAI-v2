#!/usr/bin/env python3
"""
Convenience entry point for start.py
Runs the VeritasAI unified launcher.
"""
import sys
from pathlib import Path

# Add root directory to sys.path and run start.py
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

import start

if __name__ == "__main__":
    start.main()
