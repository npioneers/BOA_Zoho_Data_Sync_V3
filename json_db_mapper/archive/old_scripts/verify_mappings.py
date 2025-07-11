import sqlite3

db_path = '../backups/json_sync_backup_20250707_222640.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('Checking mapped_CSV values in JSON mapping tables:')
print('=' * 70)

# Get a few sample mappings
cursor.execute('SELECT DISTINCT mapped_CSV FROM map_json_bills LIMIT 5')
bills_mapping = cursor.fetchone()
print(f'map_json_bills -> {bills_mapping[0] if bills_mapping else "No mapping"}')

cursor.execute('SELECT DISTINCT mapped_CSV FROM map_json_contacts LIMIT 5')
contacts_mapping = cursor.fetchone()
print(f'map_json_contacts -> {contacts_mapping[0] if contacts_mapping else "No mapping"}')

cursor.execute('SELECT DISTINCT mapped_CSV FROM map_json_invoices LIMIT 5')
invoices_mapping = cursor.fetchone()
print(f'map_json_invoices -> {invoices_mapping[0] if invoices_mapping else "No mapping"}')

cursor.execute('SELECT DISTINCT mapped_CSV FROM map_json_items LIMIT 5')
items_mapping = cursor.fetchone()
print(f'map_json_items -> {items_mapping[0] if items_mapping else "No mapping"}')

# Check organizations (should be null due to low confidence)
cursor.execute('SELECT DISTINCT mapped_CSV FROM map_json_organizations LIMIT 5')
org_mapping = cursor.fetchone()
print(f'map_json_organizations -> {org_mapping[0] if org_mapping and org_mapping[0] else "No mapping (low confidence)"}')

# Show all mappings summary
print('\nAll JSON table mappings:')
print('-' * 70)
cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE 'map_json_%' 
    ORDER BY name
''')
json_tables = [row[0] for row in cursor.fetchall()]

for table in json_tables:
    cursor.execute(f'SELECT DISTINCT mapped_CSV FROM {table} LIMIT 1')
    mapping = cursor.fetchone()
    mapped_to = mapping[0] if mapping and mapping[0] else "No mapping"
    print(f'{table:<35} -> {mapped_to}')

conn.close()
