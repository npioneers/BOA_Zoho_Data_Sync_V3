#!/usr/bin/env python3
"""
Detailed Column Mapping Error Analysis and Corrections
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 DETAILED COLUMN MAPPING ERROR ANALYSIS")
print("=" * 80)

# Define the problematic tables
error_tables = {
    "customer_payments": {
        "csv_table": "csv_customer_payments",
        "json_table": "json_customer_payments", 
        "view": "view_csv_json_customer_payments"
    },
    "vendor_payments": {
        "csv_table": "csv_vendor_payments",
        "json_table": "json_vendor_payments",
        "view": "view_csv_json_vendor_payments"
    },
    "sales_orders": {
        "csv_table": "csv_sales_orders", 
        "json_table": "json_sales_orders",
        "view": "view_csv_json_sales_orders"
    }
}

for table_name, info in error_tables.items():
    print(f"\n{'='*60}")
    print(f"🔍 ANALYZING: {table_name.upper()}")
    print(f"{'='*60}")
    
    csv_table = info["csv_table"]
    json_table = info["json_table"]
    view_name = info["view"]
    
    # Get CSV table structure
    print(f"📊 CSV TABLE STRUCTURE ({csv_table}):")
    try:
        cursor.execute(f"PRAGMA table_info({csv_table})")
        csv_columns = cursor.fetchall()
        csv_id_columns = [col[1] for col in csv_columns if 'id' in col[1].lower()]
        
        print(f"   All ID columns: {csv_id_columns}")
        
        # Find the primary key
        primary_key = None
        for col in csv_columns:
            if col[5] == 1:  # pk column in PRAGMA output
                primary_key = col[1]
                break
        
        if primary_key:
            print(f"   PRIMARY KEY: {primary_key}")
        else:
            # Guess based on naming convention
            likely_pk = [col for col in csv_id_columns if table_name.replace('_', '') in col]
            if likely_pk:
                print(f"   LIKELY PRIMARY KEY: {likely_pk[0]}")
            
    except Exception as e:
        print(f"   ❌ Error accessing CSV table: {e}")
        continue
    
    # Get JSON table structure  
    print(f"\n📊 JSON TABLE STRUCTURE ({json_table}):")
    try:
        cursor.execute(f"PRAGMA table_info({json_table})")
        json_columns = cursor.fetchall()
        json_id_columns = [col[1] for col in json_columns if 'id' in col[1].lower()]
        
        print(f"   All ID columns: {json_id_columns}")
        
        # Find the primary key
        primary_key = None
        for col in json_columns:
            if col[5] == 1:  # pk column in PRAGMA output
                primary_key = col[1]
                break
                
        if primary_key:
            print(f"   PRIMARY KEY: {primary_key}")
        else:
            # Look for obvious ID column
            obvious_ids = [col for col in json_id_columns if col.endswith('_id') and len(col.split('_')) <= 3]
            if obvious_ids:
                print(f"   LIKELY PRIMARY KEY: {obvious_ids[0]}")
                
    except Exception as e:
        print(f"   ❌ Error accessing JSON table: {e}")
        continue
    
    # Get the current problematic view SQL
    print(f"\n🔧 CURRENT VIEW DEFINITION PROBLEMS:")
    try:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{view_name}'")
        view_sql = cursor.fetchone()[0]
        
        # Extract the problematic JOIN line
        lines = view_sql.split('\n')
        join_lines = [line.strip() for line in lines if 'LEFT JOIN' in line.upper() or ('ON ' in line.upper() and '=' in line)]
        
        if join_lines:
            problematic_join = join_lines[-1]
            print(f"   CURRENT JOIN: {problematic_join}")
            
            # Identify the specific error
            if 'csv.payment_id' in problematic_join:
                print(f"   ❌ ERROR: csv.payment_id column doesn't exist")
            elif 'csv.salesorder_id' in problematic_join:
                print(f"   ❌ ERROR: csv.salesorder_id column doesn't exist")
                
    except Exception as e:
        print(f"   ❌ Error accessing view SQL: {e}")
    
    # Provide specific correction
    print(f"\n✅ RECOMMENDED CORRECTION:")
    
    if table_name == "customer_payments":
        print(f"   CURRENT (BROKEN): csv.payment_id = json.payment_id")
        print(f"   CORRECTED: csv.customer_payment_id = json.payment_id")
        print(f"   REASON: CSV uses 'customer_payment_id', JSON uses 'payment_id'")
        
    elif table_name == "vendor_payments":
        print(f"   CURRENT (BROKEN): csv.payment_id = json.payment_id") 
        print(f"   CORRECTED: csv.vendor_payment_id = json.payment_id")
        print(f"   REASON: CSV uses 'vendor_payment_id', JSON uses 'payment_id'")
        
    elif table_name == "sales_orders":
        print(f"   CURRENT (BROKEN): csv.salesorder_id = json.salesorder_id")
        print(f"   CORRECTED: csv.sales_order_id = json.salesorder_id") 
        print(f"   REASON: CSV uses 'sales_order_id', JSON uses 'salesorder_id'")
    
    # Show sample data to verify
    print(f"\n📝 SAMPLE DATA VERIFICATION:")
    try:
        if table_name == "customer_payments":
            cursor.execute(f"SELECT customer_payment_id FROM {csv_table} LIMIT 3")
            csv_samples = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SELECT payment_id FROM {json_table} LIMIT 3")
            json_samples = [row[0] for row in cursor.fetchall()]
            print(f"   CSV customer_payment_id samples: {csv_samples}")
            print(f"   JSON payment_id samples: {json_samples}")
            
        elif table_name == "vendor_payments":
            cursor.execute(f"SELECT vendor_payment_id FROM {csv_table} LIMIT 3")
            csv_samples = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SELECT payment_id FROM {json_table} LIMIT 3")
            json_samples = [row[0] for row in cursor.fetchall()]
            print(f"   CSV vendor_payment_id samples: {csv_samples}")
            print(f"   JSON payment_id samples: {json_samples}")
            
        elif table_name == "sales_orders":
            cursor.execute(f"SELECT sales_order_id FROM {csv_table} LIMIT 3")
            csv_samples = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SELECT salesorder_id FROM {json_table} LIMIT 3")
            json_samples = [row[0] for row in cursor.fetchall()]
            print(f"   CSV sales_order_id samples: {csv_samples}")
            print(f"   JSON salesorder_id samples: {json_samples}")
            
    except Exception as e:
        print(f"   ❌ Error getting samples: {e}")

print(f"\n🎯 SUMMARY OF ALL CORRECTIONS NEEDED:")
print("=" * 60)
print("1. CUSTOMER PAYMENTS:")
print("   Change: csv.payment_id → csv.customer_payment_id")
print("   JOIN: csv.customer_payment_id = json.payment_id")
print("2. VENDOR PAYMENTS:")
print("   Change: csv.payment_id → csv.vendor_payment_id")
print("   JOIN: csv.vendor_payment_id = json.payment_id")
print("3. SALES ORDERS:")
print("   Change: csv.salesorder_id → csv.sales_order_id")
print("   JOIN: csv.sales_order_id = json.salesorder_id")

print("\n🔧 IMPLEMENTATION STEPS:")
print("1. Update view definitions with correct column names")
print("2. Test the corrected JOINs work properly")
print("3. Verify data integration shows expected results")
print("4. Create FINAL views for the corrected integration views")

conn.close()
