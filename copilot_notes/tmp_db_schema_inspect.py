"""
Temporary script to inspect the schema of the Contacts table in the SQLite database.
This script is for diagnostics only and should be deleted after use.
"""
import sqlite3

DB_PATH = 'data/database/production.db'
TABLE_NAME = 'Contacts'

def print_table_schema(db_path, table_name):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        if not columns:
            print(f"Table '{table_name}' does not exist.")
            return
        print(f"Schema for table '{table_name}':")
        print("| Column Name       | Type        | Not Null | Default | Primary Key |")
        print("|-------------------|-------------|----------|---------|-------------|")
        for col in columns:
            name, col_type, notnull, dflt_value, pk = col[1], col[2], col[3], col[4], col[5]
            print(f"| {name:<17} | {col_type:<11} | {notnull!s:^8} | {str(dflt_value):<7} | {pk!s:^11} |")
    finally:
        conn.close()

if __name__ == "__main__":
    print_table_schema(DB_PATH, TABLE_NAME)
