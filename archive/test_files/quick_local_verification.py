#!/usr/bin/env python3
"""
Quick Local Data Verification

Analyzes the latest downloaded data to show:
- Start dates, end dates
- Number of records module-wise
- Line item counts
- Data summary without API calls
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

def get_latest_data_directory(base_dir: str = "data/raw_json") -> Optional[str]:
    """Find the latest timestamp directory."""
    try:
        # Handle both relative and absolute paths
        if not os.path.isabs(base_dir):
            # Try from current directory first
            data_path = Path(base_dir)
            if not data_path.exists():
                # Try from parent directory (if running from api_sync)
                data_path = Path("..") / base_dir
                if not data_path.exists():
                    # Try absolute path from script location
                    script_dir = Path(__file__).parent
                    data_path = script_dir / base_dir
                    if not data_path.exists():
                        return None
        else:
            data_path = Path(base_dir)
            
        if not data_path.exists():
            return None
            
        # Get all timestamp directories
        timestamp_dirs = []
        for item in data_path.iterdir():
            if item.is_dir() and is_timestamp_dir(item.name):
                timestamp_dirs.append(item)
                
        if not timestamp_dirs:
            return None
            
        # Return the latest one with full path
        latest = sorted(timestamp_dirs, key=lambda x: x.name)[-1]
        return str(latest)
        
    except Exception as e:
        print(f"Error finding latest directory: {e}")
        return None

def is_timestamp_dir(dirname: str) -> bool:
    """Check if directory name matches timestamp format YYYY-MM-DD_HH-MM-SS."""
    try:
        # Basic pattern check
        if len(dirname) != 19 or dirname.count('-') != 5 or dirname.count('_') != 1:
            return False
        
        # Try to parse as datetime
        datetime.strptime(dirname, '%Y-%m-%d_%H-%M-%S')
        return True
    except:
        return False

def analyze_json_file(file_path: str) -> Dict[str, Any]:
    """Analyze a JSON file and extract metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            return {"error": "File does not contain a list"}
            
        total_records = len(data)
        
        # Extract date information if available
        dates = []
        for record in data:
            if isinstance(record, dict):
                # Look for common date fields
                date_fields = ['last_modified_time', 'created_time', 'date', 'invoice_date', 'bill_date']
                for field in date_fields:
                    if field in record and record[field]:
                        try:
                            # Handle different date formats
                            date_str = record[field]
                            if 'T' in date_str:
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            dates.append(date_obj)
                            break
                        except Exception:
                            continue
        
        result = {
            "total_records": total_records,
            "date_range": None,
            "earliest_date": None,
            "latest_date": None
        }
        
        if dates:
            dates.sort()
            result["earliest_date"] = dates[0].isoformat()
            result["latest_date"] = dates[-1].isoformat()
            result["date_range"] = f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}"
            
        return result
        
    except Exception as e:
        return {"error": str(e)}

def quick_local_verification() -> Dict[str, Any]:
    """Perform quick local verification of the latest data."""
    print("🔍 Quick Local Data Verification")
    print("=" * 50)
    
    # Debug: Show current working directory
    print(f"📍 Current directory: {os.getcwd()}")
    
    # Find latest data directory
    latest_dir = get_latest_data_directory()
    if not latest_dir:
        # Try alternative paths
        possible_paths = [
            "data/raw_json",
            "../data/raw_json", 
            "./data/raw_json",
            str(Path(__file__).parent / "data/raw_json")
        ]
        print("🔍 Searching in possible paths:")
        for path in possible_paths:
            path_obj = Path(path)
            exists = path_obj.exists()
            print(f"   {path} - {'✅ EXISTS' if exists else '❌ Not found'}")
            if exists:
                # Look for timestamp directories
                timestamp_dirs = [d for d in path_obj.iterdir() if d.is_dir() and is_timestamp_dir(d.name)]
                print(f"      Found {len(timestamp_dirs)} timestamp directories")
                if timestamp_dirs:
                    latest = sorted(timestamp_dirs, key=lambda x: x.name)[-1]
                    latest_dir = str(latest)
                    print(f"      Latest: {latest.name}")
                    break
                
    if not latest_dir:
        return {"error": "No data directories found"}
        
    print(f"📁 Analyzing: {os.path.basename(latest_dir)}")
    print(f"📍 Full path: {latest_dir}")
    print()
    
    # Get all JSON files
    dir_path = Path(latest_dir)
    json_files = list(dir_path.glob("*.json"))
    
    if not json_files:
        return {"error": "No JSON files found in latest directory"}
    
    results = {}
    total_records = 0
    total_line_items = 0
    
    # Analyze each file
    for json_file in sorted(json_files):
        module_name = json_file.stem
        analysis = analyze_json_file(str(json_file))
        
        if "error" not in analysis:
            record_count = analysis["total_records"]
            total_records += record_count
            
            # Check if this is a line items file
            if "_line_items" in module_name:
                total_line_items += record_count
                
            results[module_name] = analysis
    
    # Display results
    print("📊 Module Analysis:")
    print("-" * 50)
    print(f"{'Module':<25} {'Records':<10} {'Date Range'}")
    print("-" * 50)
    
    # Regular modules first
    regular_modules = []
    line_item_modules = []
    
    for module_name, data in results.items():
        if "_line_items" in module_name:
            line_item_modules.append((module_name, data))
        else:
            regular_modules.append((module_name, data))
    
    # Display regular modules
    for module_name, data in sorted(regular_modules):
        count = data.get("total_records", 0)
        date_range = data.get("date_range", "No dates found")
        print(f"{module_name:<25} {count:<10} {date_range}")
    
    if line_item_modules:
        print()
        print("📋 Line Items:")
        print("-" * 30)
        for module_name, data in sorted(line_item_modules):
            count = data.get("total_records", 0)
            date_range = data.get("date_range", "No dates found")
            base_module = module_name.replace("_line_items", "")
            print(f"{base_module} line items: {count} records")
            if date_range != "No dates found":
                print(f"  Date range: {date_range}")
    
    print()
    print("📈 Summary:")
    print("-" * 20)
    print(f"Total header records: {total_records - total_line_items}")
    print(f"Total line items: {total_line_items}")
    print(f"Total records: {total_records}")
    print(f"Modules analyzed: {len([m for m in results.keys() if '_line_items' not in m])}")
    
    # Find overall date range
    all_earliest = []
    all_latest = []
    
    for data in results.values():
        if data.get("earliest_date"):
            all_earliest.append(datetime.fromisoformat(data["earliest_date"]))
        if data.get("latest_date"):
            all_latest.append(datetime.fromisoformat(data["latest_date"]))
    
    if all_earliest and all_latest:
        overall_earliest = min(all_earliest)
        overall_latest = max(all_latest)
        print(f"Overall date range: {overall_earliest.strftime('%Y-%m-%d')} to {overall_latest.strftime('%Y-%m-%d')}")
    
    return {
        "success": True,
        "directory": latest_dir,
        "modules": results,
        "summary": {
            "total_header_records": total_records - total_line_items,
            "total_line_items": total_line_items,
            "total_records": total_records,
            "modules_count": len([m for m in results.keys() if '_line_items' not in m])
        }
    }

if __name__ == "__main__":
    try:
        result = quick_local_verification()
        if not result.get("success"):
            print(f"❌ Error: {result.get('error')}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
