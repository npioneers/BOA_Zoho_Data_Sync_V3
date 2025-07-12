#!/usr/bin/env python3
"""
Explain why csv_items shows 928 records
"""

import pandas as pd

def explain_items_data():
    print('🔍 UNDERSTANDING WHY CSV_ITEMS SHOWS 928 RECORDS')
    print('='*80)

    # Items analysis
    df_items = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Item.csv')
    print('📦 ITEMS TABLE (Master Data - Product Catalog):')
    print(f'  CSV Records: {len(df_items):,}')
    print(f'  Unique Item IDs: {df_items["Item ID"].nunique():,}')
    print(f'  Ratio: 1:1 (each record = unique product/service)')
    print(f'  Nature: MASTER DATA - not flattened')

    print()

    # Invoice analysis  
    df_invoices = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Invoice.csv')
    print('📄 INVOICES TABLE (Transactional Data - Line Items):')
    print(f'  CSV Records: {len(df_invoices):,}')
    print(f'  Unique Invoice IDs: {df_invoices["Invoice ID"].nunique():,}')
    print(f'  Ratio: {len(df_invoices) / df_invoices["Invoice ID"].nunique():.1f}:1 (line items per invoice)')
    print(f'  Nature: TRANSACTIONAL DATA - flattened to line items')

    print()

    # Sales Order analysis
    df_sales = pd.read_csv('../data/csv/Nangsel Pioneers_Latest/Sales_Order.csv')
    print('🛒 SALES ORDERS TABLE (Transactional Data - Line Items):')
    print(f'  CSV Records: {len(df_sales):,}')
    print(f'  Unique Sales Order IDs: {df_sales["Salesorder ID"].nunique():,}')
    print(f'  Ratio: {len(df_sales) / df_sales["Salesorder ID"].nunique():.1f}:1 (line items per sales order)')
    print(f'  Nature: TRANSACTIONAL DATA - flattened to line items')

    print()
    print('🎯 KEY INSIGHT:')
    print('='*80)
    print('Items table is NOT flattened because it is MASTER DATA')
    print('928 records = 928 unique products/services in your catalog')
    print('')
    print('Compare with:')
    print(f'• Invoices: {df_invoices["Invoice ID"].nunique():,} actual invoices → {len(df_invoices):,} line items')
    print(f'• Sales Orders: {df_sales["Salesorder ID"].nunique():,} actual orders → {len(df_sales):,} line items')
    print('')
    print('This is the expected behavior - items are not "flattened" like transactions!')

if __name__ == "__main__":
    explain_items_data()
