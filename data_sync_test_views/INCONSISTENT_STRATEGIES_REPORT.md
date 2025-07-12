# FINAL Views Duplicate Handling Strategy Analysis Report

## Executive Summary

Analysis of 9 FINAL views reveals **three distinct duplicate handling strategies** with significant inconsistencies across similar business entities.

## Strategy Classification

### Strategy 1: LEFT JOIN + COALESCE (Sophisticated Merging) ✅
**4 views (44.4%) - Financial Document Views**
- `FINAL_view_csv_json_bills`
- `FINAL_view_csv_json_credit_notes` 
- `FINAL_view_csv_json_invoices`
- `FINAL_view_csv_json_purchase_orders`

**Characteristics:**
- Uses LEFT JOIN to combine CSV and JSON tables
- Uses COALESCE to prioritize data sources
- Handles duplicates intelligently by merging records
- Maintains data integrity across both sources

### Strategy 2: CSV-ONLY (JSON Data Ignored) ❌
**5 views (55.6%) - Master Data & Payment Views**
- `FINAL_view_csv_json_contacts` 
- `FINAL_view_csv_json_customer_payments`
- `FINAL_view_csv_json_items`
- `FINAL_view_csv_json_sales_orders`
- `FINAL_view_csv_json_vendor_payments`

**Characteristics:**
- Only selects from CSV tables: `SELECT * FROM csv_[table]`
- Completely ignores corresponding JSON data
- Sets `data_source = 'CSV'` or `'csv_only'`
- Assigns `source_priority = 2` or `3`
- **CRITICAL ISSUE: Missing JSON records entirely**

### Strategy 3: UNION-Based (Expected but Not Found)
**0 views (0%) - Not Implemented**
- No views use UNION to combine CSV and JSON sources
- This would be the most comprehensive approach for full data visibility

## Data Loss Analysis

### Missing JSON Records
The CSV-only views completely ignore JSON data sources:

| View | CSV Records | JSON Records Available | Data Loss |
|------|-------------|------------------------|-----------|
| contacts | 224 | ~14 (estimated) | JSON contacts invisible |
| customer_payments | 1,744 | Unknown | JSON payments invisible |
| items | 928 | ~1,114 (estimated) | JSON items invisible |
| sales_orders | 5,751 | Unknown | JSON orders invisible |
| vendor_payments | 530 | Unknown | JSON payments invisible |

## Inconsistency Issues

### 1. Different Approaches for Similar Business Entities
- **Financial Documents**: Use sophisticated LEFT JOIN + COALESCE
- **Master Data**: Use simple CSV-only selection
- **Payments**: Split approach (inconsistent)

### 2. Missing Standardization
- No consistent duplicate handling methodology
- Different `source_priority` values (2 vs 3)
- Different `data_source` labeling ('CSV' vs 'csv_only')

### 3. Business Logic Gaps
- Payment entities treated differently:
  - Customer/Vendor payments: CSV-only
  - But Bills/Invoices (also payment-related): LEFT JOIN + COALESCE
- Master data (contacts, items) completely ignore JSON enrichment

## Recommendations

### 1. Immediate: Fix CSV-Only Views
Convert the 5 CSV-only views to use LEFT JOIN + COALESCE pattern:
```sql
-- Example fix for contacts
CREATE VIEW FINAL_view_csv_json_contacts AS
SELECT 
    COALESCE(json.contact_id, csv.contact_id) as contact_id,
    COALESCE(json.display_name, csv.display_name) as display_name,
    -- ... other fields
    CASE 
        WHEN json.contact_id IS NOT NULL THEN 'JSON'
        ELSE 'CSV' 
    END as data_source,
    CASE 
        WHEN json.contact_id IS NOT NULL THEN 1
        ELSE 2 
    END as source_priority
FROM csv_contacts csv
LEFT JOIN json_contacts json ON csv.contact_id = json.contact_id
WHERE COALESCE(json.display_name, csv.display_name) IS NOT NULL
```

### 2. Medium-term: Standardize All Views
- Apply consistent LEFT JOIN + COALESCE pattern across all 9 views
- Standardize source_priority: JSON=1, CSV=2
- Standardize data_source labeling

### 3. Long-term: Consider UNION Approach
For complete data visibility, implement UNION-based views:
```sql
-- Complete data visibility approach
SELECT *, 'JSON' as data_source, 1 as source_priority FROM json_contacts
UNION
SELECT *, 'CSV' as data_source, 2 as source_priority 
FROM csv_contacts 
WHERE contact_id NOT IN (SELECT contact_id FROM json_contacts WHERE contact_id IS NOT NULL)
```

## Impact Assessment

### Current State Issues
1. **Data Blindness**: 55.6% of views ignore JSON data completely
2. **Inconsistent Business Logic**: Similar entities handled differently  
3. **Missing Records**: Unknown number of JSON-only records invisible
4. **User Confusion**: Different data sources for similar business processes

### Post-Fix Benefits
1. **Complete Data Visibility**: All records from both CSV and JSON sources
2. **Consistent User Experience**: Same logic across all business entities
3. **Better Data Quality**: JSON data often more detailed/recent
4. **Future-Proof**: Ready for API-first data architecture

## Technical Implementation Priority

### High Priority (Fix Immediately)
- `FINAL_view_csv_json_contacts` - Master data loss
- `FINAL_view_csv_json_items` - Significant JSON item data loss

### Medium Priority
- `FINAL_view_csv_json_customer_payments`
- `FINAL_view_csv_json_vendor_payments` 
- `FINAL_view_csv_json_sales_orders`

### Validation Required
- Verify JSON table existence and record counts
- Test duplicate handling with actual data overlaps
- Confirm business rules for data source priority
