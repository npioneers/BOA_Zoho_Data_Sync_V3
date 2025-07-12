#!/usr/bin/env python3
"""
Analyze database tables and their date columns for business date prioritization
"""

import sqlite3
import os
from json2db_config import JSON2DBSyncConfig

def analyze_database_structure():
    """Analyze the database structure and identify appropriate date columns"""
    
    # Load configuration and get database path
    try:
        config = JSON2DBSyncConfig()
        db_path = config.get_database_path()
        
        if not db_path.exists():
            print(f"❌ Database not found at configured path: {db_path}")
            print(f"   Please check your configuration or create the database first")
            return
            
        print(f"✅ Using database from configuration: {db_path}")
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📊 Total tables: {len(tables)}")
    print("=" * 80)
    
    # Business date field priorities for each table type
    business_date_mapping = {}
    
    for table in sorted(tables):
        # Get columns for each table
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Find all date-related columns
        date_cols = [col for col in columns if any(d in col.lower() 
                    for d in ['date', 'time', 'created', 'modified', 'updated'])]
        
        # Determine business date priority based on table name
        business_date = determine_business_date_priority(table, date_cols)
        business_date_mapping[table] = business_date
        
        print(f"\n🏷️  TABLE: {table}")
        print(f"   📅 Date columns: {date_cols}")
        print(f"   ⭐ Recommended business date: {business_date['primary']}")
        if business_date['fallback']:
            print(f"   🔄 Fallback dates: {business_date['fallback']}")
        print(f"   📝 Reasoning: {business_date['reasoning']}")
    
    conn.close()
    
    # Generate the implementation code
    generate_implementation_code(business_date_mapping)
    
    return business_date_mapping

def determine_business_date_priority(table_name, date_columns):
    """Determine the appropriate business date priority for a table"""
    
    table_lower = table_name.lower()
    
    # Business-specific date mappings
    if 'invoice' in table_lower:
        primary = find_column_match(date_columns, ['invoice_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Invoice date represents the actual business transaction date"
        
    elif 'bill' in table_lower:
        primary = find_column_match(date_columns, ['bill_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Bill date represents when the bill was issued"
        
    elif 'salesorder' in table_lower:
        primary = find_column_match(date_columns, ['salesorder_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Sales order date represents when the order was placed"
        
    elif 'purchaseorder' in table_lower:
        primary = find_column_match(date_columns, ['purchaseorder_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Purchase order date represents when the order was created"
        
    elif 'creditnote' in table_lower:
        primary = find_column_match(date_columns, ['creditnote_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Credit note date represents when the credit was issued"
        
    elif 'payment' in table_lower or 'customerpayment' in table_lower or 'vendorpayment' in table_lower:
        primary = find_column_match(date_columns, ['payment_date', 'date'])
        fallback = find_columns_match(date_columns, ['created_time', 'last_modified_time'])
        reasoning = "Payment date represents when the payment was made"
        
    elif 'contact' in table_lower:
        primary = find_column_match(date_columns, ['date', 'created_time'])
        fallback = find_columns_match(date_columns, ['last_modified_time', 'updated_time'])
        reasoning = "Contacts rarely have business dates, use creation date as primary"
        
    elif 'item' in table_lower:
        primary = find_column_match(date_columns, ['date', 'created_time'])
        fallback = find_columns_match(date_columns, ['last_modified_time', 'updated_time'])
        reasoning = "Items rarely have business dates, use creation date as primary"
        
    elif 'line_item' in table_lower:
        # Line items should inherit from their parent document
        primary = find_column_match(date_columns, ['date', 'created_time'])
        fallback = find_columns_match(date_columns, ['last_modified_time'])
        reasoning = "Line items inherit date context from parent document"
        
    else:
        # Generic fallback logic
        primary = find_column_match(date_columns, ['date', 'created_time', 'last_modified_time'])
        fallback = find_columns_match(date_columns, ['updated_time', 'modified_time'])
        reasoning = "Generic table - using most common date field pattern"
    
    return {
        'primary': primary,
        'fallback': fallback,
        'reasoning': reasoning
    }

def find_column_match(columns, preferred_names):
    """Find the first matching column from a list of preferred names"""
    for pref in preferred_names:
        if pref in columns:
            return pref
    return None

def find_columns_match(columns, preferred_names):
    """Find all matching columns from a list of preferred names"""
    matches = []
    for pref in preferred_names:
        if pref in columns:
            matches.append(pref)
    return matches

def generate_implementation_code(business_date_mapping):
    """Generate the implementation code for the business date logic"""
    
    print("\n" + "="*80)
    print("🔧 IMPLEMENTATION CODE GENERATION")
    print("="*80)
    
    print("\n📝 Function to add to runner_json2db_sync.py:")
    print("""
def _get_business_date_column(self, table_name: str, columns: List[str]) -> Optional[str]:
    \"\"\"Get the most appropriate business date column for a table\"\"\"
    
    table_lower = table_name.lower()
    
    # Business date priority mapping""")
    
    for table, mapping in business_date_mapping.items():
        if mapping['primary']:
            table_type = get_table_type(table)
            print(f"    # {table}: {mapping['reasoning']}")
    
    print("""    
    # 1. Document-specific business dates (HIGHEST PRIORITY)
    if 'invoice' in table_lower:
        for col in ['invoice_date', 'date']:
            if col in columns: return col
                
    elif 'bill' in table_lower:
        for col in ['bill_date', 'date']:
            if col in columns: return col
            
    elif 'salesorder' in table_lower:
        for col in ['salesorder_date', 'date']:
            if col in columns: return col
            
    elif 'purchaseorder' in table_lower:
        for col in ['purchaseorder_date', 'date']:
            if col in columns: return col
            
    elif 'creditnote' in table_lower:
        for col in ['creditnote_date', 'date']:
            if col in columns: return col
            
    elif any(term in table_lower for term in ['payment', 'customerpayment', 'vendorpayment']):
        for col in ['payment_date', 'date']:
            if col in columns: return col
    
    # 2. Generic business date (MEDIUM PRIORITY)
    if 'date' in columns:
        return 'date'
    
    # 3. System dates (LOWEST PRIORITY - only if no business date)
    for sys_date in ['created_time', 'last_modified_time', 'updated_time', 'modified_time']:
        if sys_date in columns:
            return sys_date
            
    return None""")

def get_table_type(table_name):
    """Get the business type of a table"""
    table_lower = table_name.lower()
    
    if 'invoice' in table_lower:
        return 'invoice'
    elif 'bill' in table_lower:
        return 'bill'
    elif 'salesorder' in table_lower:
        return 'salesorder'
    elif 'purchaseorder' in table_lower:
        return 'purchaseorder'
    elif 'creditnote' in table_lower:
        return 'creditnote'
    elif 'payment' in table_lower:
        return 'payment'
    elif 'contact' in table_lower:
        return 'contact'
    elif 'item' in table_lower:
        return 'item'
    else:
        return 'generic'

if __name__ == "__main__":
    analyze_database_structure()
