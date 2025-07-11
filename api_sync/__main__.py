"""
API Sync Package Main Entry Point

Allows running the package as a module: python -m api_sync
"""

from .cli import main

if __name__ == '__main__':
    exit(main())
