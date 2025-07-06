"""
Temporary script to add the missing CustomerSubType column to the Contacts table.
This script is for diagnostics and migration only. Delete after use.
"""
import sqlite3

DB_PATH = 'data/database/production.db'
TABLE_NAME = 'Contacts'
COLUMN_NAME = 'CustomerSubType'
COLUMN_TYPE = 'TEXT'

def add_column_if_missing(db_path, table_name, column_name, column_type):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        if column_name in columns:
            print(f"Column '{column_name}' already exists in '{table_name}'. No action taken.")
            return
        # Add the column
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        conn.commit()
        print(f"Column '{column_name}' added to '{table_name}'.")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column_if_missing(DB_PATH, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE)
