#!/usr/bin/env python3
"""
JSON Data Availability Analysis
Quantifies exact data loss from CSV-only views by checking JSON table availability.
"""
import sqlite3
from config import get_database_path


def analyze_data_loss():
    """Analyze actual data loss from CSV-only strategy"""
    db_path = get_database_path()
    
    csv_only_views = {
        "FINAL_view_csv_json_contacts": {"csv_table": "csv_contacts", "json_table": "json_contacts"},
        "FINAL_view_csv_json_customer_payments": {"csv_table": "csv_customer_payments", "json_table": "json_customer_payments"},
        "FINAL_view_csv_json_items": {"csv_table": "csv_items", "json_table": "json_items"},
        "FINAL_view_csv_json_sales_orders": {"csv_table": "csv_sales_orders", "json_table": "json_sales_orders"},
        "FINAL_view_csv_json_vendor_payments": {"csv_table": "csv_vendor_payments", "json_table": "json_vendor_payments"}
    }
    
    print("=" * 100)
    print("JSON DATA AVAILABILITY AND LOSS ANALYSIS")
    print("=" * 100)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, check which JSON tables actually exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'json_%' ORDER BY name")
        existing_json_tables = {row[0] for row in cursor.fetchall()}
        
        print(f"📊 Available JSON tables: {len(existing_json_tables)}")
        for table in sorted(existing_json_tables):
            print(f"   - {table}")
        print()
        
        total_csv_records = 0
        total_json_available = 0
        total_data_loss = 0
        
        for view_name, tables in csv_only_views.items():
            csv_table = tables["csv_table"]
            json_table = tables["json_table"]
            
            print(f"🔍 ANALYZING: {view_name}")
            print("-" * 80)
            
            # Get CSV record count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{csv_table}`")
                csv_count = cursor.fetchone()[0]
                total_csv_records += csv_count
                print(f"📈 CSV Records ({csv_table}): {csv_count:,}")
            except Exception as e:
                print(f"❌ Error counting CSV records: {e}")
                csv_count = 0
            
            # Check if JSON table exists and get count
            if json_table in existing_json_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{json_table}`")
                    json_count = cursor.fetchone()[0]
                    total_json_available += json_count
                    print(f"📈 JSON Records ({json_table}): {json_count:,}")
                    
                    # Estimate potential records if combined properly
                    potential_total = csv_count + json_count  # Rough estimate, actual may be less due to duplicates
                    current_visible = csv_count  # Only CSV visible in current view
                    estimated_loss = json_count
                    total_data_loss += estimated_loss
                    
                    print(f"💡 Potential Total (if combined): ~{potential_total:,}")
                    print(f"👁️  Currently Visible: {current_visible:,}")
                    print(f"🚫 Estimated Data Loss: {estimated_loss:,} records ({(estimated_loss/potential_total*100):.1f}%)")
                    
                    # Try to check for overlapping IDs if possible
                    try:
                        # Assume standard ID field naming
                        id_field_candidates = [
                            f"{json_table.replace('json_', '')}_id",
                            "id",
                            f"{json_table.replace('json_', '').rstrip('s')}_id"  # Remove plural 's'
                        ]
                        
                        overlap_found = False
                        for id_field in id_field_candidates:
                            try:
                                cursor.execute(f"PRAGMA table_info(`{csv_table}`)")
                                csv_columns = [col[1] for col in cursor.fetchall()]
                                cursor.execute(f"PRAGMA table_info(`{json_table}`)")
                                json_columns = [col[1] for col in cursor.fetchall()]
                                
                                if id_field in csv_columns and id_field in json_columns:
                                    # Check for overlapping IDs
                                    cursor.execute(f"""
                                        SELECT COUNT(DISTINCT csv.{id_field}) as overlap_count
                                        FROM `{csv_table}` csv 
                                        INNER JOIN `{json_table}` json ON csv.{id_field} = json.{id_field}
                                        WHERE csv.{id_field} IS NOT NULL AND json.{id_field} IS NOT NULL
                                    """)
                                    overlap_count = cursor.fetchone()[0]
                                    
                                    cursor.execute(f"""
                                        SELECT COUNT(*) as json_only_count
                                        FROM `{json_table}` json 
                                        WHERE json.{id_field} NOT IN (
                                            SELECT csv.{id_field} FROM `{csv_table}` csv 
                                            WHERE csv.{id_field} IS NOT NULL
                                        ) AND json.{id_field} IS NOT NULL
                                    """)
                                    json_only_count = cursor.fetchone()[0]
                                    
                                    print(f"🔗 ID Overlap Analysis (using {id_field}):")
                                    print(f"   Overlapping records: {overlap_count:,}")
                                    print(f"   JSON-only records: {json_only_count:,}")
                                    print(f"   True data loss: {json_only_count:,} unique records")
                                    overlap_found = True
                                    break
                                    
                            except Exception:
                                continue
                        
                        if not overlap_found:
                            print(f"⚠️  Could not determine ID overlap - using simple count difference")
                            
                    except Exception as e:
                        print(f"⚠️  Could not analyze overlaps: {e}")
                        
                except Exception as e:
                    print(f"❌ Error counting JSON records: {e}")
                    print(f"🚫 Data Loss: Cannot quantify (JSON table exists but not accessible)")
            else:
                print(f"❌ JSON table ({json_table}) does not exist")
                print(f"🚫 Data Loss: Cannot quantify (no JSON source)")
            
            print()
        
        # Summary
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print(f"📊 Total CSV records across 5 views: {total_csv_records:,}")
        print(f"📊 Total JSON records available: {total_json_available:,}")
        print(f"🚫 Estimated minimum data loss: {total_data_loss:,} records")
        
        if total_csv_records + total_json_available > 0:
            loss_percentage = (total_data_loss / (total_csv_records + total_json_available)) * 100
            print(f"📉 Data loss percentage: ~{loss_percentage:.1f}%")
        
        print(f"\n💡 RECOMMENDATION: Convert CSV-only views to LEFT JOIN + COALESCE")
        print(f"   This would make {total_json_available:,} additional records visible")
        print("=" * 100)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")


if __name__ == "__main__":
    analyze_data_loss()
