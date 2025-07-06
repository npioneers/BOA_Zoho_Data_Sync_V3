# data_sync_app/src/data_sync/processing/raw_data_handler.py

import os
import json
from typing import List, Dict, Any

def save_raw_json(data: List[Dict[str, Any]], module_name: str, run_timestamp_str: str):
    """
    Saves the fetched raw data to a timestamped JSON file.

    Args:
        data: The list of records (as dicts) fetched from the API.
        module_name: The name of the Zoho module (e.g., 'invoices').
        run_timestamp_str: A string representing the current sync run's start time,
                             used for creating a unique folder.
    """
    if not data:
        print(f"INFO: No new raw data to save for module '{module_name}'.")
        return

    try:
        # Define the path for the timestamped output directory
        output_dir = os.path.join('output', 'raw_json', run_timestamp_str)
        
        # Create the directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"INFO: Created/verified directory: {output_dir}")
        except OSError as dir_error:
            print(f"ERROR: Failed to create directory '{output_dir}': {dir_error}")
            return

        # Define the full path for the output file
        file_path = os.path.join(output_dir, f"{module_name}.json")

        print(f"INFO: Saving {len(data)} raw records for '{module_name}' to {file_path}")

        # Write the data to the file with indentation for readability
        # Use context manager to ensure proper file closure
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"SUCCESS: Raw JSON saved for '{module_name}'")
        except (IOError, OSError) as file_error:
            print(f"ERROR: Could not write file '{file_path}': {file_error}")
            return

    except IOError as e:
        print(f"ERROR: Could not write raw JSON file for '{module_name}'.")
        print(f"  - I/O Error: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during raw JSON saving: {e}")
