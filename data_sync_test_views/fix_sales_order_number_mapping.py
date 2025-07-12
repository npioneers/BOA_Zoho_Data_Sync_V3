import sqlite3

def fix_sales_order_number_mapping():
    """
    Fix the sales order number field mapping issue by:
    1. Creating a unified sales order number field
    2. Updating integration and FINAL views
    3. Implementing proper data source handling
    """
    
    # Connect to database
    conn = sqlite3.connect('../data/database/production.db')
    
    print("🔧 FIXING SALES ORDER NUMBER FIELD MAPPING")
    print("=" * 60)
    
    try:
        # 1. First, let's check the current view structure and backup
        print("\n📊 1. BACKING UP CURRENT VIEW DEFINITIONS:")
        print("-" * 50)
        
        # Get current view definitions
        current_integration_view = conn.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='view' AND name='view_csv_json_sales_orders'
        """).fetchone()
        
        current_final_view = conn.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='view' AND name='FINAL_view_csv_json_sales_orders'
        """).fetchone()
        
        print("✅ Current views backed up in memory")
        
        # 2. Drop existing views
        print("\n📊 2. DROPPING EXISTING VIEWS FOR RECREATION:")
        print("-" * 50)
        
        conn.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        conn.execute("DROP VIEW IF EXISTS view_csv_json_sales_orders")
        print("✅ Existing views dropped")
        
        # 3. Create improved integration view with unified sales order number
        print("\n📊 3. CREATING IMPROVED INTEGRATION VIEW:")
        print("-" * 50)
        
        new_integration_view = """
        CREATE VIEW view_csv_json_sales_orders AS
        SELECT
            -- Unified sales order number field (PRIMARY FIX)
            COALESCE(json.salesorder_number, csv.sales_order_number) AS unified_sales_order_number,
            
            -- Original fields with proper COALESCE
            COALESCE(json.branch_id, csv.branch_id) AS branch_id,
            COALESCE(json.branch_name, csv.branch_name) AS branch_name,
            COALESCE(json.cf_region, csv.cf_region) AS cf_region,
            COALESCE(json.currency_code, csv.currency_code) AS currency_code,
            COALESCE(json.customer_id, csv.customer_id) AS customer_id,
            COALESCE(json.customer_name, csv.customer_name) AS customer_name,
            COALESCE(json.data_source, csv.data_source) AS data_source,
            COALESCE(json.delivery_method, csv.delivery_method) AS delivery_method,
            COALESCE(json.quantity_invoiced, csv.quantity_invoiced) AS quantity_invoiced,
            COALESCE(json.reference_number, csv.reference_number) AS reference_number,
            COALESCE(json.source, csv.source) AS source,
            COALESCE(json.status, csv.status) AS status,
            COALESCE(json.total, csv.total) AS total,
            
            -- CSV-specific fields
            csv.account,
            csv.account_code,
            csv.adjustment,
            csv.adjustment_description,
            csv.billing_address,
            csv.billing_city,
            csv.billing_code,
            csv.billing_country,
            csv.billing_fax,
            csv.billing_phone,
            csv.billing_state,
            csv.billing_street2,
            csv.cf_pending_items_delivery,
            csv.created_timestamp,
            csv.custom_status,
            csv.discount,
            csv.discount_amount,
            csv.discount_type,
            csv.entity_discount_amount,
            csv.entity_discount_percent,
            csv.exchange_rate,
            csv.expected_shipment_date,
            csv.is_discount_before_tax,
            csv.is_inclusive_tax,
            csv.item_cf_sku_category,
            csv.item_desc,
            csv.item_name,
            csv.item_price,
            csv.item_tax,
            csv.item_tax_amount,
            csv.item_tax_percent,
            csv.item_tax_type,
            csv.item_total,
            csv.kit_combo_item_name,
            csv.notes,
            csv.order_date,
            csv.payment_terms,
            csv.payment_terms_label,
            csv.product_id,
            csv.project_id,
            csv.project_name,
            csv.quantity_cancelled,
            csv.quantity_ordered,
            csv.region,
            csv.sales_order_id,
            csv.sales_order_number,
            csv.sales_person,
            csv.shipping_address,
            csv.shipping_charge,
            csv.shipping_charge_tax_amount,
            csv.shipping_charge_tax_id,
            csv.shipping_charge_tax_name,
            csv.shipping_charge_tax_percent,
            csv.shipping_charge_tax_type,
            csv.shipping_city,
            csv.shipping_code,
            csv.shipping_country,
            csv.shipping_fax,
            csv.shipping_phone,
            csv.shipping_state,
            csv.shipping_street2,
            csv.sku,
            csv.subtotal,
            csv.tax_id,
            csv.tds_amount,
            csv.tds_name,
            csv.tds_percentage,
            csv.tds_type,
            csv.template_name,
            csv.terms_conditions,
            csv.updated_timestamp,
            csv.usage_unit,
            csv.vehicle,
            
            -- JSON-specific fields
            json.bcy_total,
            json.cf_region_unformatted,
            json.color_code,
            json.company_name,
            json.created_time,
            json.currency_id,
            json.current_sub_status,
            json.current_sub_status_id,
            json.custom_fields_list,
            json.date,
            json.delivery_date,
            json.delivery_method_id,
            json.due_by_days,
            json.due_in_days,
            json.email,
            json.has_attachment,
            json.invoiced_status,
            json.invoiced_sub_status,
            json.invoiced_sub_status_id,
            json.is_emailed,
            json.is_manually_fulfilled,
            json.is_scheduled_for_quick_shipment_create,
            json.is_viewed_in_mail,
            json.last_modified_time,
            json.location_id,
            json.mail_first_viewed_time,
            json.mail_last_viewed_time,
            json.order_fulfillment_type,
            json.order_status,
            json.order_sub_status,
            json.order_sub_status_id,
            json.paid_status,
            json.pickup_location_id,
            json.salesorder_id,
            json.salesorder_number,
            json.salesperson_name,
            json.shipment_date,
            json.shipment_days,
            json.shipped_status,
            json.tags,
            json.total_invoiced_amount,
            json.zcrm_potential_id,
            json.zcrm_potential_name,
            
            -- Data source tracking
            CASE WHEN json.salesorder_id IS NOT NULL THEN 'json' ELSE 'csv' END AS data_source,
            CASE WHEN json.salesorder_id IS NOT NULL THEN 1 ELSE 2 END AS source_priority,
            
            -- Data quality flags
            CASE 
                WHEN csv.sales_order_number IS NOT NULL AND csv.sales_order_number != '' AND csv.sales_order_number != 'None' THEN 'csv_has_number'
                ELSE 'csv_no_number'
            END AS csv_number_quality,
            CASE 
                WHEN json.salesorder_number IS NOT NULL AND json.salesorder_number != '' THEN 'json_has_number'
                ELSE 'json_no_number'
            END AS json_number_quality
            
        FROM csv_sales_orders csv
        LEFT JOIN json_sales_orders json ON csv.sales_order_id = json.salesorder_id

        UNION ALL

        SELECT
            -- Unified sales order number field
            json.salesorder_number AS unified_sales_order_number,
            
            json.branch_id,
            json.branch_name,
            json.cf_region,
            json.currency_code,
            json.customer_id,
            json.customer_name,
            json.data_source,
            json.delivery_method,
            json.quantity_invoiced,
            json.reference_number,
            json.source,
            json.status,
            json.total,
            
            -- CSV fields (NULL for JSON-only records)
            NULL as account,
            NULL as account_code,
            NULL as adjustment,
            NULL as adjustment_description,
            NULL as billing_address,
            NULL as billing_city,
            NULL as billing_code,
            NULL as billing_country,
            NULL as billing_fax,
            NULL as billing_phone,
            NULL as billing_state,
            NULL as billing_street2,
            NULL as cf_pending_items_delivery,
            NULL as created_timestamp,
            NULL as custom_status,
            NULL as discount,
            NULL as discount_amount,
            NULL as discount_type,
            NULL as entity_discount_amount,
            NULL as entity_discount_percent,
            NULL as exchange_rate,
            NULL as expected_shipment_date,
            NULL as is_discount_before_tax,
            NULL as is_inclusive_tax,
            NULL as item_cf_sku_category,
            NULL as item_desc,
            NULL as item_name,
            NULL as item_price,
            NULL as item_tax,
            NULL as item_tax_amount,
            NULL as item_tax_percent,
            NULL as item_tax_type,
            NULL as item_total,
            NULL as kit_combo_item_name,
            NULL as notes,
            NULL as order_date,
            NULL as payment_terms,
            NULL as payment_terms_label,
            NULL as product_id,
            NULL as project_id,
            NULL as project_name,
            NULL as quantity_cancelled,
            NULL as quantity_ordered,
            NULL as region,
            NULL as sales_order_id,
            NULL as sales_order_number,
            NULL as sales_person,
            NULL as shipping_address,
            NULL as shipping_charge,
            NULL as shipping_charge_tax_amount,
            NULL as shipping_charge_tax_id,
            NULL as shipping_charge_tax_name,
            NULL as shipping_charge_tax_percent,
            NULL as shipping_charge_tax_type,
            NULL as shipping_city,
            NULL as shipping_code,
            NULL as shipping_country,
            NULL as shipping_fax,
            NULL as shipping_phone,
            NULL as shipping_state,
            NULL as shipping_street2,
            NULL as sku,
            NULL as subtotal,
            NULL as tax_id,
            NULL as tds_amount,
            NULL as tds_name,
            NULL as tds_percentage,
            NULL as tds_type,
            NULL as template_name,
            NULL as terms_conditions,
            NULL as updated_timestamp,
            NULL as usage_unit,
            NULL as vehicle,
            
            -- JSON fields
            json.bcy_total,
            json.cf_region_unformatted,
            json.color_code,
            json.company_name,
            json.created_time,
            json.currency_id,
            json.current_sub_status,
            json.current_sub_status_id,
            json.custom_fields_list,
            json.date,
            json.delivery_date,
            json.delivery_method_id,
            json.due_by_days,
            json.due_in_days,
            json.email,
            json.has_attachment,
            json.invoiced_status,
            json.invoiced_sub_status,
            json.invoiced_sub_status_id,
            json.is_emailed,
            json.is_manually_fulfilled,
            json.is_scheduled_for_quick_shipment_create,
            json.is_viewed_in_mail,
            json.last_modified_time,
            json.location_id,
            json.mail_first_viewed_time,
            json.mail_last_viewed_time,
            json.order_fulfillment_type,
            json.order_status,
            json.order_sub_status,
            json.order_sub_status_id,
            json.paid_status,
            json.pickup_location_id,
            json.salesorder_id,
            json.salesorder_number,
            json.salesperson_name,
            json.shipment_date,
            json.shipment_days,
            json.shipped_status,
            json.tags,
            json.total_invoiced_amount,
            json.zcrm_potential_id,
            json.zcrm_potential_name,
            
            'json' AS data_source,
            1 AS source_priority,
            'csv_no_number' AS csv_number_quality,
            'json_has_number' AS json_number_quality
            
        FROM json_sales_orders json
        WHERE json.salesorder_id NOT IN (
            SELECT DISTINCT csv.sales_order_id
            FROM csv_sales_orders csv
            WHERE csv.sales_order_id IS NOT NULL
        )
        """
        
        conn.execute(new_integration_view)
        print("✅ New integration view created with unified_sales_order_number field")
        
        # 4. Create improved FINAL view
        print("\n📊 4. CREATING IMPROVED FINAL VIEW:")
        print("-" * 50)
        
        new_final_view = """
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT * FROM view_csv_json_sales_orders
        """
        
        conn.execute(new_final_view)
        print("✅ New FINAL view created")
        
        # 5. Test the new views
        print("\n📊 5. TESTING NEW VIEW FUNCTIONALITY:")
        print("-" * 50)
        
        # Test unified sales order number field
        test_query = conn.execute("""
        SELECT 
            unified_sales_order_number,
            data_source,
            csv_number_quality,
            json_number_quality,
            COUNT(*) as count
        FROM FINAL_view_csv_json_sales_orders
        WHERE unified_sales_order_number IS NOT NULL AND unified_sales_order_number != '' AND unified_sales_order_number != 'None'
        GROUP BY unified_sales_order_number, data_source, csv_number_quality, json_number_quality
        ORDER BY count DESC
        LIMIT 10
        """).fetchall()
        
        print("📋 Unified Sales Order Numbers Working:")
        for row in test_query:
            print(f"  SO: '{row[0]}' | Source: {row[1]} | CSV Quality: {row[2]} | JSON Quality: {row[3]} | Count: {row[4]}")
        
        # Check total records with populated unified numbers
        total_unified = conn.execute("""
        SELECT COUNT(*) 
        FROM FINAL_view_csv_json_sales_orders
        WHERE unified_sales_order_number IS NOT NULL AND unified_sales_order_number != '' AND unified_sales_order_number != 'None'
        """).fetchone()[0]
        
        total_records = conn.execute("SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders").fetchone()[0]
        
        print(f"\n📊 Summary:")
        print(f"  Total records: {total_records}")
        print(f"  Records with unified sales order numbers: {total_unified}")
        print(f"  Coverage: {total_unified/total_records*100:.1f}%")
        
        # 6. Test searching for the missing sales orders
        print("\n📊 6. TESTING MISSING SALES ORDERS SEARCH:")
        print("-" * 50)
        
        missing_orders = ["SO-00572", "SO/25-26/00793"]
        
        for order_num in missing_orders:
            matches = conn.execute("""
            SELECT unified_sales_order_number, data_source, customer_name
            FROM FINAL_view_csv_json_sales_orders
            WHERE unified_sales_order_number LIKE ?
            """, (f"%{order_num}%",)).fetchall()
            
            print(f"  '{order_num}': {len(matches)} matches")
            for match in matches:
                print(f"    - SO: '{match[0]}' | Source: {match[1]} | Customer: '{match[2]}'")
        
        # Commit changes
        conn.commit()
        print("\n✅ All changes committed successfully!")
        
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        conn.rollback()
        print("🔄 Changes rolled back")
        
        # Try to restore original views if possible
        if 'current_integration_view' in locals() and current_integration_view:
            try:
                conn.execute(current_integration_view[0])
                print("✅ Original integration view restored")
            except:
                pass
                
        if 'current_final_view' in locals() and current_final_view:
            try:
                conn.execute(current_final_view[0])
                print("✅ Original FINAL view restored")
            except:
                pass
    
    finally:
        conn.close()
    
    print("\n🎯 SALES ORDER NUMBER FIELD MAPPING FIX COMPLETE")
    print("📋 New unified_sales_order_number field provides proper sales order identification")

if __name__ == "__main__":
    fix_sales_order_number_mapping()
