"""
Main entry point for JSON-to-DB sync as a script.

This script allows running the JSON sync pipeline directly (not via CLI subcommands),
for integration with test runners or as a simple entry point for automation.
"""

from src.json_sync.cli import main

if __name__ == "__main__":
    exit(main())
