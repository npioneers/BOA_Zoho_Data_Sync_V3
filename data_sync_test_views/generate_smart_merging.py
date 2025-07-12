#!/usr/bin/env python3
"""
Smart Merging View Generator
Creates LEFT JOIN + COALESCE view definitions for CSV-only views to fix data loss.
"""
import sqlite3
from typing import Dict, List, Tuple
from config import get_database_path


class SmartMergingGenerator:
    """Generates smart merging SQL for CSV-only views"""
    
    def __init__(self):
        self.db_path = get_database_path()
        self.csv_only_views = [
            "FINAL_view_csv_json_contacts",
            "FINAL_view_csv_json_customer_payments", 
            "FINAL_view_csv_json_items",
            "FINAL_view_csv_json_sales_orders",
            "FINAL_view_csv_json_vendor_payments"
        ]
        
    def get_table_schema(self, table_name: str) -> List[Tuple[str, str]]:
        """Get column names and types for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = [(row[1], row[2]) for row in cursor.fetchall()]
            
            conn.close()
            return columns
            
        except Exception as e:
            print(f"❌ Error getting schema for {table_name}: {e}")
            return []
    
    def identify_key_column(self, view_name: str) -> str:
        """Identify the primary key column for joining tables"""
        # Extract entity name from view name
        entity = view_name.replace("FINAL_view_csv_json_", "")
        
        key_mappings = {
            "contacts": "contact_id",
            "customer_payments": "customer_payment_id", 
            "items": "item_id",
            "sales_orders": "sales_order_id",
            "vendor_payments": "vendor_payment_id"
        }
        
        return key_mappings.get(entity, f"{entity}_id")
    
    def get_common_columns(self, csv_table: str, json_table: str) -> List[str]:
        """Get columns that exist in both CSV and JSON tables"""
        csv_columns = {col[0] for col in self.get_table_schema(csv_table)}
        json_columns = {col[0] for col in self.get_table_schema(json_table)}
        
        # Find common columns (excluding data_source which we'll handle separately)
        common = csv_columns.intersection(json_columns)
        if 'data_source' in common:
            common.remove('data_source')
            
        return sorted(list(common))
    
    def generate_smart_view_sql(self, view_name: str) -> str:
        """Generate smart merging SQL for a view"""
        entity = view_name.replace("FINAL_view_csv_json_", "")
        csv_table = f"csv_{entity}"
        json_table = f"json_{entity}"
        key_column = self.identify_key_column(view_name)
        
        print(f"📝 Generating smart merge for {view_name}")
        print(f"   CSV Table: {csv_table}")
        print(f"   JSON Table: {json_table}")
        print(f"   Key Column: {key_column}")
        
        # Get schemas
        csv_columns = {col[0]: col[1] for col in self.get_table_schema(csv_table)}
        json_columns = {col[0]: col[1] for col in self.get_table_schema(json_table)}
        
        if not csv_columns:
            return f"-- ERROR: Could not get schema for {csv_table}"
        if not json_columns:
            return f"-- WARNING: JSON table {json_table} not found, keeping CSV-only"
        
        print(f"   CSV Columns: {len(csv_columns)}")
        print(f"   JSON Columns: {len(json_columns)}")
        
        # Get all unique columns from both tables
        all_columns = set(csv_columns.keys()) | set(json_columns.keys())
        
        # Remove data_source as we'll handle it specially
        if 'data_source' in all_columns:
            all_columns.remove('data_source')
        
        # Generate COALESCE statements for each column
        select_clauses = []
        
        for column in sorted(all_columns):
            csv_has = column in csv_columns
            json_has = column in json_columns
            
            if csv_has and json_has:
                # Both tables have the column - use COALESCE with JSON priority
                select_clauses.append(f"    COALESCE(json.{column}, csv.{column}) AS {column}")
            elif json_has:
                # Only JSON has the column
                select_clauses.append(f"    json.{column}")
            elif csv_has:
                # Only CSV has the column
                select_clauses.append(f"    csv.{column}")
        
        # Add data source and priority columns
        select_clauses.extend([
            "    (CASE",
            "        WHEN json.{} IS NOT NULL THEN 'JSON'".format(key_column),
            "        ELSE 'CSV'",
            "    END) AS data_source",
            "    (CASE", 
            "        WHEN json.{} IS NOT NULL THEN 1".format(key_column),
            "        ELSE 2",
            "    END) AS source_priority"
        ])
        
        # Join clauses with commas, except the last one
        formatted_clauses = []
        for i, clause in enumerate(select_clauses):
            if i < len(select_clauses) - 1:
                formatted_clauses.append(clause + ",")
            else:
                formatted_clauses.append(clause)
        
        # Generate WHERE clause based on entity type
        where_clauses = self.generate_where_clause(entity, csv_table, json_table)
        
        # Construct the complete SQL
        sql = f"""CREATE VIEW {view_name} AS
SELECT
{chr(10).join(formatted_clauses)}
FROM {csv_table} csv
LEFT JOIN {json_table} json ON csv.{key_column} = json.{key_column}
{where_clauses}"""
        
        return sql
    
    def generate_where_clause(self, entity: str, csv_table: str, json_table: str) -> str:
        """Generate appropriate WHERE clause for different entity types"""
        where_conditions = {
            "contacts": [
                "COALESCE(json.display_name, csv.display_name) IS NOT NULL",
                "OR COALESCE(json.company_name, csv.company_name) IS NOT NULL", 
                "OR COALESCE(json.first_name, csv.first_name) IS NOT NULL",
                "OR COALESCE(json.last_name, csv.last_name) IS NOT NULL"
            ],
            "customer_payments": [
                "COALESCE(json.payment_number, csv.payment_number) IS NOT NULL"
            ],
            "items": [
                "COALESCE(json.item_name, csv.item_name) IS NOT NULL",
                "OR COALESCE(json.sku, csv.sku) IS NOT NULL",
                "OR COALESCE(json.description, csv.description) IS NOT NULL"
            ],
            "sales_orders": [
                "COALESCE(json.sales_order_number, csv.sales_order_number) IS NOT NULL",
                "OR COALESCE(json.customer_name, csv.customer_name) IS NOT NULL",
                "OR COALESCE(json.order_date, csv.order_date) IS NOT NULL"
            ],
            "vendor_payments": [
                "COALESCE(json.payment_number, csv.payment_number) IS NOT NULL"
            ]
        }
        
        conditions = where_conditions.get(entity, [])
        if conditions:
            # Join conditions with proper indentation
            where_clause = "WHERE\n    " + "\n    ".join(conditions)
            return where_clause
        else:
            return ""
    
    def generate_all_smart_views(self) -> Dict[str, str]:
        """Generate smart merging SQL for all CSV-only views"""
        results = {}
        
        print("=" * 80)
        print("SMART MERGING VIEW GENERATOR")
        print("=" * 80)
        
        for view_name in self.csv_only_views:
            print(f"\n🔄 Processing {view_name}")
            sql = self.generate_smart_view_sql(view_name)
            results[view_name] = sql
            print(f"✅ Generated SQL ({len(sql)} characters)")
        
        return results
    
    def save_sql_to_file(self, sql_dict: Dict[str, str], filename: str = "smart_merging_views.sql"):
        """Save generated SQL to file"""
        with open(filename, 'w') as f:
            f.write("-- Smart Merging Views SQL\n")
            f.write("-- Generated to fix CSV-only views and eliminate JSON data loss\n")
            f.write("-- Replaces simple CSV SELECT with LEFT JOIN + COALESCE pattern\n\n")
            
            for view_name, sql in sql_dict.items():
                f.write(f"-- =============================================================================\n")
                f.write(f"-- {view_name}\n")
                f.write(f"-- Fixes data loss by merging CSV and JSON sources with JSON priority\n")
                f.write(f"-- =============================================================================\n\n")
                f.write(f"DROP VIEW IF EXISTS {view_name};\n\n")
                f.write(f"{sql};\n\n")
        
        print(f"\n💾 SQL saved to: {filename}")
    
    def preview_improvements(self, sql_dict: Dict[str, str]):
        """Preview the improvements that will be made"""
        print("\n" + "=" * 80)
        print("PREVIEW OF IMPROVEMENTS")
        print("=" * 80)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for view_name in self.csv_only_views:
                entity = view_name.replace("FINAL_view_csv_json_", "")
                csv_table = f"csv_{entity}"
                json_table = f"json_{entity}"
                
                print(f"\n📊 {view_name}")
                
                # Get current record count
                cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
                current_count = cursor.fetchone()[0]
                
                # Get CSV and JSON counts
                cursor.execute(f"SELECT COUNT(*) FROM `{csv_table}`")
                csv_count = cursor.fetchone()[0]
                
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{json_table}`")
                    json_count = cursor.fetchone()[0]
                except:
                    json_count = 0
                
                potential_total = csv_count + json_count  # Simplified estimate
                improvement = json_count
                
                print(f"   Current records: {current_count:,}")
                print(f"   CSV records: {csv_count:,}")
                print(f"   JSON records: {json_count:,}")
                print(f"   Potential total: ~{potential_total:,}")
                print(f"   Expected improvement: +{improvement:,} records")
                
                if json_count > 0:
                    improvement_pct = (improvement / current_count * 100) if current_count > 0 else 0
                    print(f"   Improvement: {improvement_pct:.1f}% more data visible")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error generating preview: {e}")


def main():
    """Main function to generate smart merging views"""
    generator = SmartMergingGenerator()
    
    # Generate all smart view SQL
    sql_dict = generator.generate_all_smart_views()
    
    # Preview improvements
    generator.preview_improvements(sql_dict)
    
    # Save to file
    generator.save_sql_to_file(sql_dict)
    
    print("\n" + "=" * 80)
    print("✅ SMART MERGING GENERATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the generated SQL in smart_merging_views.sql")
    print("2. Test the views in a development environment")
    print("3. Apply to production database when ready")
    print("4. Verify data improvements with updated analysis")


if __name__ == "__main__":
    main()
