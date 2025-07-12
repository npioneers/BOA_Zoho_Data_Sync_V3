import pandas as pd

# Items - Master Data
df_items = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Item.csv')
print(f'ITEMS: {len(df_items)} records, {df_items["Item ID"].nunique()} unique items')

# Invoices - Transactional Data (flattened)
df_invoices = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Invoice.csv')
print(f'INVOICES: {len(df_invoices)} records, {df_invoices["Invoice ID"].nunique()} unique invoices')
print(f'Invoice ratio: {len(df_invoices) / df_invoices["Invoice ID"].nunique():.1f} line items per invoice')

print('\nCONCLUSION:')
print('Items = 928 records because it is MASTER DATA (product catalog)')
print('Each record = 1 unique product, not flattened like transactions')
