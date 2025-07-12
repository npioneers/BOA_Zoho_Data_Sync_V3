#!/usr/bin/env python3
"""
Display the exact database path being used for verification
"""
import os
from pathlib import Path

def get_database_paths():
    """Get all possible database paths"""
    
    print("=== DATABASE PATH ANALYSIS ===")
    print()
    
    # Current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    print()
    
    # Possible database locations
    possible_paths = [
        # Relative to current directory (csv_db_rebuild)
        "../data/database/production.db",
        "data/database/production.db",
        
        # Relative to project root
        "../../data/database/production.db", 
        
        # Absolute paths based on project structure
        "c:/Users/User/Documents/Projects/Automated_Operations/Zoho_Data_Sync_V3/data/database/production.db",
        "c:\\Users\\User\\Documents\\Projects\\Automated_Operations\\Zoho_Data_Sync_V3\\data\\database\\production.db",
        
        # Other common locations
        "../production.db",
        "production.db"
    ]
    
    print("CHECKING POSSIBLE DATABASE LOCATIONS:")
    print("-" * 50)
    
    existing_databases = []
    
    for db_path in possible_paths:
        abs_path = Path(db_path).resolve()
        exists = abs_path.exists()
        size = ""
        
        if exists:
            try:
                size_bytes = abs_path.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                size = f" ({size_mb:.1f} MB)"
                existing_databases.append(str(abs_path))
            except:
                size = " (error reading size)"
        
        status = "✅ EXISTS" if exists else "❌ NOT FOUND"
        print(f"{status} {db_path}")
        print(f"    Absolute: {abs_path}{size}")
        print()
    
    print("EXISTING DATABASES FOUND:")
    print("-" * 30)
    if existing_databases:
        for i, db_path in enumerate(existing_databases, 1):
            print(f"{i}. {db_path}")
    else:
        print("No production.db files found!")
    
    print()
    
    # Check default CSV rebuild configuration
    print("DEFAULT CSV REBUILD CONFIGURATION:")
    print("-" * 40)
    
    try:
        import sys
        sys.path.append('.')
        from runner_csv_db_rebuild import CSVDatabaseRebuildRunner
        
        # Create runner with default settings
        runner = CSVDatabaseRebuildRunner()
        default_db_path = runner.db_path
        
        print(f"Default database path: {default_db_path}")
        print(f"Absolute path: {Path(default_db_path).resolve()}")
        print(f"Database exists: {Path(default_db_path).exists()}")
        
        if Path(default_db_path).exists():
            size_bytes = Path(default_db_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            print(f"Database size: {size_mb:.1f} MB")
        
    except Exception as e:
        print(f"Error getting default configuration: {e}")
    
    print()
    print("=" * 60)
    
    return existing_databases

if __name__ == "__main__":
    databases = get_database_paths()
    
    if databases:
        print(f"RECOMMENDATION: Use this database path for verification:")
        print(f"'{databases[0]}'")
    else:
        print("ERROR: No production.db database found!")
        print("Please check if the database exists or create it first.")
