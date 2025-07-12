#!/usr/bin/env python3

import sqlite3
from pathlib import Path

db_path = Path('data/database/production.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check json_invoices - should show 2025-07-12 as the latest date
    print('🔍 Checking json_invoices latest data:')
    cursor.execute('SELECT date, last_modified_time FROM json_invoices ORDER BY last_modified_time DESC LIMIT 5')
    rows = cursor.fetchall()
    for invoice_date, modified_time in rows:
        print(f'  Invoice Date: {invoice_date}, Modified: {modified_time}')

    print('\n🔍 Checking json_bills latest data:')
    cursor.execute('SELECT date, last_modified_time FROM json_bills ORDER BY last_modified_time DESC LIMIT 5')
    rows = cursor.fetchall()
    for bill_date, modified_time in rows:
        print(f'  Bill Date: {bill_date}, Modified: {modified_time}')

    print('\n🔍 Checking json_contacts latest data:')
    cursor.execute('SELECT last_modified_time FROM json_contacts ORDER BY last_modified_time DESC LIMIT 5')
    rows = cursor.fetchall()
    for modified_time, in rows:
        print(f'  Modified: {modified_time}')

except Exception as e:
    print(f'Error: {e}')
    # List available columns
    cursor.execute('PRAGMA table_info(json_invoices)')
    columns = cursor.fetchall()
    print('Available columns in json_invoices:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

conn.close()
