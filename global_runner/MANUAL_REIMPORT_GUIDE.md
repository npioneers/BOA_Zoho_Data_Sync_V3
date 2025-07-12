# Manual Re-import Guide - CSV Tables with Fixed Compound Word Mapping

**Date:** July 12, 2025  
**Status:** Compound word fix applied ✅  
**Action Required:** Manual re-import of 8 affected tables

## 🎯 Quick Re-import Commands

### Priority 1: Critical Business Identifiers
```powershell
# Navigate to CSV rebuild directory
cd csv_db_rebuild

# Re-import sales orders (SalesOrder Number, SalesOrder ID)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_sales_orders
# Then:   3. Populate Single Table -> csv_sales_orders

# Re-import customer payments (CustomerPayment ID, CustomerID)  
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_customer_payments
# Then:   3. Populate Single Table -> csv_customer_payments
```

### Priority 2: Order Management
```powershell
# Re-import purchase orders (Quantity fields)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_purchase_orders
# Then:   3. Populate Single Table -> csv_purchase_orders
```

### Priority 3: Contact & Payment Data
```powershell
# Re-import contacts (EmailID, MobilePhone)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_contacts
# Then:   3. Populate Single Table -> csv_contacts

# Re-import vendor payments (VendorPayment ID, EmailID)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_vendor_payments
# Then:   3. Populate Single Table -> csv_vendor_payments
```

### Priority 4: Remaining Tables
```powershell
# Re-import invoices (PurchaseOrder, EmailID, PortCode)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_invoices
# Then:   3. Populate Single Table -> csv_invoices

# Re-import bills (PurchaseOrder)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_bills
# Then:   3. Populate Single Table -> csv_bills

# Re-import credit notes (CreditNotes ID)
python main_csv_db_rebuild.py
# Select: 5. Clear Single Table -> csv_credit_notes
# Then:   3. Populate Single Table -> csv_credit_notes
```

## ✅ Verification After Each Re-import

### Test Sales Orders (Priority)
```sql
-- Check SalesOrder Number population
SELECT COUNT(*) as total_records, 
       COUNT(sales_order_number) as populated_numbers,
       COUNT(sales_order_number) * 100.0 / COUNT(*) as population_rate
FROM csv_sales_orders;

-- Verify specific sales order exists
SELECT sales_order_id, sales_order_number, order_date, status 
FROM csv_sales_orders 
WHERE sales_order_number LIKE '%SO/25-26/00808%' 
LIMIT 5;
```

### Test Customer Payments
```sql
-- Check CustomerPayment ID and CustomerID population
SELECT COUNT(*) as total_records,
       COUNT(customer_payment_id) as payment_ids,
       COUNT(customer_id) as customer_ids
FROM csv_customer_payments;
```

### Test Purchase Orders
```sql
-- Check Quantity fields population
SELECT COUNT(*) as total_records,
       COUNT(quantity_ordered) as qty_ordered,
       COUNT(quantity_received) as qty_received
FROM csv_purchase_orders;
```

## 🎯 Expected Results After Fix

| Table | Key Fields to Verify | Expected Population |
|-------|---------------------|-------------------|
| `csv_sales_orders` | `sales_order_number`, `sales_order_id` | 100% (5,751 records) |
| `csv_customer_payments` | `customer_payment_id`, `customer_id` | 100% (3,400 records) |
| `csv_purchase_orders` | `quantity_ordered`, `quantity_received` | 100% (2,900 records) |
| `csv_contacts` | `email_id`, `mobile_phone` | Variable% (450 records) |
| `csv_vendor_payments` | `vendor_payment_id`, `email_id` | 100% (1,050 records) |
| `csv_invoices` | `purchase_order`, `email_id` | Variable% (7,000 records) |
| `csv_bills` | `purchase_order` | Variable% (3,100 records) |
| `csv_credit_notes` | `credit_notes_id` | 100% (1,500 records) |

## 🚨 Validation Checklist

After re-importing priority tables, verify:

- [ ] `sales_order_number` field shows values like "SO-00009", "SO/25-26/00808"
- [ ] `customer_payment_id` field populated with payment identifiers  
- [ ] `customer_id` field populated with customer identifiers
- [ ] `quantity_ordered`, `quantity_received` fields show numeric values
- [ ] Historical sales order `SO/25-26/00808` appears in search results
- [ ] No NULL/empty values in critical business identifier fields

## 📞 Success Indicators

✅ **Complete Success**: All compound word fields populate to expected rates  
✅ **Business Functions**: Can track orders, customers, payments by ID  
✅ **Historical Data**: Target sales orders like `SO/25-26/00808` accessible  
✅ **Global Runner Ready**: CSV rebuild package ready for integration

---

**Note**: The csv_items table had no compound word issues and doesn't need re-import.
