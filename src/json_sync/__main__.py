"""
JSON Sync Package Main Entry Point

Allows running the package as a module:
python -m src.json_sync [command] [options]
"""

from .cli import main

if __name__ == '__main__':
    exit(main())
