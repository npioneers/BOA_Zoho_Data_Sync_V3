#!/usr/bin/env python3
"""
Debug SQL Syntax
Tests SQL generation to identify syntax issues.
"""
import sqlite3
from config import get_database_path


def test_simple_view():
    """Test a simple view creation"""
    db_path = get_database_path()
    
    # Simple test view
    test_sql = """
CREATE VIEW test_simple_view AS
SELECT
    csv.contact_id,
    csv.contact_name,
    json.contact_type,
    COALESCE(json.company_name, csv.company_name) AS company_name,
    CASE
        WHEN json.contact_id IS NOT NULL THEN 'JSON'
        ELSE 'CSV'
    END AS data_source,
    CASE
        WHEN json.contact_id IS NOT NULL THEN 1
        ELSE 2
    END AS source_priority
FROM csv_contacts csv
LEFT JOIN json_contacts json ON csv.contact_id = json.contact_id
WHERE
    COALESCE(json.company_name, csv.company_name) IS NOT NULL
    OR COALESCE(json.contact_name, csv.contact_name) IS NOT NULL
"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🧪 Testing simple view creation...")
        print("SQL:")
        print(test_sql)
        print()
        
        # Drop if exists
        cursor.execute("DROP VIEW IF EXISTS test_simple_view")
        
        # Create view
        cursor.execute(test_sql)
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM test_simple_view")
        count = cursor.fetchone()[0]
        
        print(f"✅ View created successfully")
        print(f"📊 Record count: {count}")
        
        # Test data source distribution
        cursor.execute("SELECT data_source, COUNT(*) FROM test_simple_view GROUP BY data_source")
        distribution = dict(cursor.fetchall())
        print(f"📈 Data sources: {distribution}")
        
        # Clean up
        cursor.execute("DROP VIEW test_simple_view")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def extract_and_test_contacts_view():
    """Extract and test the contacts view SQL"""
    
    # Read the generated SQL file
    try:
        with open("smart_merging_views.sql", 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read SQL file: {e}")
        return False
    
    # Find the contacts view
    start_marker = "CREATE VIEW FINAL_view_csv_json_contacts AS"
    end_marker = "FROM csv_contacts csv"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("❌ Could not find contacts view")
        return False
    
    # Find the end of the SELECT clause (before FROM)
    from_idx = content.find(end_marker, start_idx)
    if from_idx == -1:
        print("❌ Could not find FROM clause")
        return False
    
    # Extract just the SELECT portion
    select_portion = content[start_idx:from_idx].strip()
    
    print("🔍 Generated SELECT clause:")
    print(select_portion)
    print()
    
    # Count commas and find potential issues
    lines = select_portion.split('\n')
    print("📝 Line analysis:")
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith('--'):
            has_comma = line.endswith(',')
            print(f"  {i+1:2d}: {line} {'✓' if has_comma or 'SELECT' in line or 'AS' in line else '❌'}")
    
    return True


def main():
    """Main debug function"""
    print("=" * 80)
    print("SQL SYNTAX DEBUGGING")
    print("=" * 80)
    
    print("\n1. Testing simple view creation...")
    if test_simple_view():
        print("✅ Simple view test passed")
    else:
        print("❌ Simple view test failed")
    
    print("\n2. Analyzing generated SQL...")
    extract_and_test_contacts_view()


if __name__ == "__main__":
    main()
