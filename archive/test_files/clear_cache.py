#!/usr/bin/env python3
"""
Clear Python __pycache__ directories

This script removes __pycache__ directories and .pyc files to force Python
to recompile modules on next import.
"""

import os
import shutil
from pathlib import Path

def clear_pycache(directory):
    """Clear __pycache__ directories and .pyc files in the given directory."""
    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            pycache_dir = os.path.join(root, "__pycache__")
            print(f"Removing {pycache_dir}")
            shutil.rmtree(pycache_dir)
        
        # Remove .pyc files
        for file in files:
            if file.endswith(".pyc"):
                pyc_file = os.path.join(root, file)
                print(f"Removing {pyc_file}")
                os.remove(pyc_file)

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent
    
    print(f"Clearing Python cache in {project_root}")
    clear_pycache(project_root)
    print("Cache cleared.")
