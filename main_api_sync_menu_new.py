#!/usr/bin/env python3
"""
Main API Sync Entry Point

This script serves as the root-level entry point that delegates to 
the actual wrapper located in the api_sync package.
"""

import sys
import os

def main():
    """Main entry point that delegates to the api_sync package."""
    try:
        # Import and run the actual wrapper from api_sync package
        from api_sync.main_api_sync import main as api_sync_main
        return api_sync_main()
    except ImportError as e:
        print(f"❌ Error importing api_sync package: {e}")
        print("Ensure you're running from the project root directory.")
        return False
    except Exception as e:
        print(f"❌ Error running API sync: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
