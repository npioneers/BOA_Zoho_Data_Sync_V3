#!/usr/bin/env python3
"""
Categorize All Tables by Pattern Type
"""
import sqlite3
from config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🎯 TABLE CATEGORIZATION BY PATTERN")
print("=" * 60)

# Define the categories based on our analysis
categories = {
    "LINE_ITEM_EXPANSION": {
        "description": "CSV headers + JSON line items = massive expansion",
        "pattern": "✅ CSV foundation + JSON enrichment (NO changes needed)",
        "tables": []
    },
    "CSV_PREFERRED_IMPLEMENTED": {
        "description": "Already implemented CSV-preferred strategy",
        "pattern": "✅ Working correctly with our improvements",
        "tables": []
    },
    "CSV_ONLY_CORRECT": {
        "description": "CSV-only data, JSON has no overlap",
        "pattern": "✅ Correct behavior, no JSON data to merge",
        "tables": []
    },
    "JSON_ONLY_CORRECT": {
        "description": "JSON-only data, CSV has no overlap", 
        "pattern": "✅ Correct behavior, no CSV data to merge",
        "tables": []
    },
    "COLUMN_MAPPING_ERRORS": {
        "description": "Views fail due to column name mismatches",
        "pattern": "❌ Needs key column mapping fixes",
        "tables": []
    },
    "NO_DATA": {
        "description": "Empty or minimal data",
        "pattern": "⚪ Not applicable",
        "tables": []
    }
}

# Analyze each table from our previous results
analysis_results = {
    "view_csv_json_bills": {
        "csv": 3218, "json": 72, "view_total": 154336,
        "distribution": {"csv_only": 2885, "enhanced": 151451},
        "expansion": 46.9, "pattern": "LINE_ITEM_EXPANSION"
    },
    "view_csv_json_invoices": {
        "csv": 6933, "json": 2811, "view_total": 192547,
        "distribution": {"csv_only": 6066, "enhanced": 186481},
        "expansion": 19.8, "pattern": "LINE_ITEM_EXPANSION"
    },
    "view_csv_json_items": {
        "csv": 928, "json": 1114, "view_total": 2042,
        "distribution": {"csv": 928, "json": 1114},
        "expansion": 1.0, "pattern": "CSV_PREFERRED_IMPLEMENTED"
    },
    "view_csv_json_contacts": {
        "csv": 224, "json": 14, "view_total": 14,
        "distribution": {"json": 14},
        "expansion": 0.06, "pattern": "JSON_ONLY_CORRECT"
    },
    "view_csv_json_credit_notes": {
        "csv": 756, "json": 143, "view_total": 756,
        "distribution": {"csv": 756},
        "expansion": 0.84, "pattern": "CSV_ONLY_CORRECT"
    },
    "view_csv_json_purchase_orders": {
        "csv": 2982, "json": 30, "view_total": 2982,
        "distribution": {"csv": 2982},
        "expansion": 0.99, "pattern": "CSV_ONLY_CORRECT"
    },
    "view_csv_json_organizations": {
        "csv": 0, "json": 3, "view_total": 0,
        "distribution": {},
        "expansion": 0, "pattern": "NO_DATA"
    },
    "view_csv_json_customer_payments": {
        "csv": 1744, "json": 84, "view_total": "ERROR",
        "distribution": {},
        "error": "no such column: csv.payment_id",
        "pattern": "COLUMN_MAPPING_ERRORS"
    },
    "view_csv_json_sales_orders": {
        "csv": 5751, "json": 387, "view_total": "ERROR",
        "distribution": {},
        "error": "no such column: csv.salesorder_id",
        "pattern": "COLUMN_MAPPING_ERRORS"
    },
    "view_csv_json_vendor_payments": {
        "csv": 530, "json": 13, "view_total": "ERROR",
        "distribution": {},
        "error": "no such column: csv.payment_id",
        "pattern": "COLUMN_MAPPING_ERRORS"
    }
}

# Categorize tables
for table, data in analysis_results.items():
    pattern = data["pattern"]
    categories[pattern]["tables"].append({
        "name": table.replace("view_csv_json_", ""),
        "data": data
    })

# Display categorized results
for category, info in categories.items():
    if info["tables"]:
        print(f"\n📋 {category}")
        print(f"   {info['description']}")
        print(f"   {info['pattern']}")
        print(f"   Tables ({len(info['tables'])}):")
        
        for table in info["tables"]:
            name = table["name"]
            data = table["data"]
            
            if "error" in data:
                print(f"      • {name}: ERROR - {data['error']}")
            else:
                csv_count = data.get("csv", 0)
                json_count = data.get("json", 0)
                view_total = data.get("view_total", 0)
                expansion = data.get("expansion", 0)
                
                print(f"      • {name}: CSV={csv_count:,}, JSON={json_count:,}, View={view_total:,} ({expansion:.1f}x)")
                
                if data.get("distribution"):
                    dist_str = ", ".join([f"{k}:{v:,}" for k, v in data["distribution"].items()])
                    print(f"        Distribution: {dist_str}")

print(f"\n🎯 SUMMARY BY PATTERN:")
for category, info in categories.items():
    if info["tables"]:
        count = len(info["tables"])
        print(f"   {category}: {count} table(s)")

print(f"\n💡 RECOMMENDATIONS:")
print("✅ LINE_ITEM_EXPANSION: No changes needed - perfect CSV+JSON integration")
print("✅ CSV_PREFERRED_IMPLEMENTED: Already optimized with our improvements")
print("✅ CSV/JSON_ONLY_CORRECT: Working as expected, no overlap to merge")
print("❌ COLUMN_MAPPING_ERRORS: Fix key column name mismatches")
print("⚪ NO_DATA: Monitor for future data population")

conn.close()
