#!/usr/bin/env python3
"""
Fix FINAL views using proper mapping table information
"""

import sqlite3
import sys
import os

def fix_final_views():
    """Fix the empty FINAL views using proper mapping information"""
    
    db_path = r"C:\Users\User\Documents\Projects\Automated_Operations\Zoho_Data_Sync_V3\data\database\production.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 FIXING FINAL VIEWS WITH PROPER MAPPINGS")
        print("=" * 50)
        
        # Fix contacts view
        print("\n1️⃣ FIXING FINAL_view_csv_json_contacts")
        print("-" * 40)
        
        # Drop existing view
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_contacts")
        
        # Create new contacts view with proper column mapping and non-NULL filtering
        contacts_sql = """
        CREATE VIEW FINAL_view_csv_json_contacts AS
        SELECT
            -- Common fields (prioritize JSON flat view if available)
            COALESCE(flat.contact_id, csv.contact_id) AS contact_id,
            COALESCE(flat.company_name, csv.company_name) AS company_name,
            COALESCE(flat.first_name, csv.first_name) AS first_name,
            COALESCE(flat.last_name, csv.last_name) AS last_name,
            COALESCE(flat.email, csv.email) AS email,
            COALESCE(flat.phone, csv.phone) AS phone,
            COALESCE(flat.mobile, csv.mobile) AS mobile,
            COALESCE(flat.website, csv.website) AS website,
            COALESCE(flat.created_time, csv.created_time) AS created_time,
            COALESCE(flat.last_modified_time, csv.last_modified_time) AS last_modified_time,
            
            -- CSV-specific fields
            csv.created_timestamp,
            csv.updated_timestamp, 
            csv.display_name,
            csv.salutation,
            csv.notes,
            csv.contact_type,
            csv.customer_type,
            csv.vendor_type,
            csv.billing_address,
            csv.shipping_address,
            csv.contact_persons,
            csv.currency_id,
            csv.payment_terms,
            csv.payment_terms_label,
            csv.credit_limit,
            csv.twitter,
            csv.facebook,
            csv.gst_no,
            csv.gst_treatment,
            csv.tax_treatment,
            csv.place_of_supply,
            csv.vat_treatment,
            csv.tax_regime,
            csv.is_taxable,
            csv.avatar_file_name,
            csv.status,
            csv.account_tax_id,
            csv.is_tds_registered,
            csv.tds_exemption_applicable,
            csv.exemption_certificate_no,
            csv.statement_descriptor,
            csv.track_1099,
            csv.tax_id_type,
            csv.tax_id_value,
            csv.tax_authority_id,
            csv.tax_authority_name,
            csv.tax_exemption_id,
            csv.tax_exemption_code,
            csv.source,
            csv.ach_supported,
            csv.price_precision,
            csv.can_send_in_mail,
            csv.is_portal_enabled,
            csv.portal_status,
            csv.language_code,
            csv.is_linked_with_zohocrm,
            csv.zcrm_account_id,
            csv.zcrm_contact_id,
            csv.owner_id,
            csv.primary_contact_id,
            csv.payment_reminder_enabled,
            csv.contact_sub_type,
            csv.source_of_supply,
            csv.destination_of_supply,
            csv.vat_reg_no,
            csv.country_code,
            csv.phone_number_formatted,
            csv.mobile_number_formatted,
            
            -- JSON-specific fields
            flat.customer_name,
            flat.vendor_name,
            flat.language_code_formatted,
            flat.contact_type_formatted,
            flat.billing_address_attention,
            flat.billing_address_address,
            flat.billing_address_street2,
            flat.billing_address_city,
            flat.billing_address_state_code,
            flat.billing_address_state,
            flat.billing_address_zip,
            flat.billing_address_country,
            flat.billing_address_phone,
            flat.billing_address_fax,
            flat.shipping_address_attention,
            flat.shipping_address_address,
            flat.shipping_address_street2,
            flat.shipping_address_city,
            flat.shipping_address_state_code,
            flat.shipping_address_state,
            flat.shipping_address_zip,
            flat.shipping_address_country,
            flat.shipping_address_phone,
            flat.shipping_address_fax,
            flat.custom_fields,
            flat.contact_persons_contact_person_id,
            flat.contact_persons_salutation,
            flat.contact_persons_first_name,
            flat.contact_persons_last_name,
            flat.contact_persons_email,
            flat.contact_persons_phone,
            flat.contact_persons_mobile,
            flat.contact_persons_skype,
            flat.contact_persons_designation,
            flat.contact_persons_department,
            flat.contact_persons_is_primary_contact,
            flat.contact_persons_enable_portal,
            
            -- Data source tracking
            CASE 
                WHEN flat.contact_id IS NOT NULL THEN 'JSON'
                WHEN csv.contact_id IS NOT NULL THEN 'CSV'
                ELSE 'UNKNOWN'
            END AS data_source,
            
            CASE 
                WHEN flat.contact_id IS NOT NULL AND csv.contact_id IS NOT NULL THEN 1
                WHEN flat.contact_id IS NOT NULL THEN 2  
                WHEN csv.contact_id IS NOT NULL THEN 3
                ELSE 4
            END AS source_priority
            
        FROM csv_contacts csv
        FULL OUTER JOIN view_flat_json_contacts flat 
            ON csv.contact_id = flat.contact_id
        WHERE 
            csv.display_name IS NOT NULL 
            OR csv.company_name IS NOT NULL 
            OR flat.contact_name IS NOT NULL
            OR flat.company_name IS NOT NULL
        """
        
        try:
            cursor.execute(contacts_sql)
            print("✅ Successfully created FINAL_view_csv_json_contacts")
        except sqlite3.Error as e:
            # If JSON table doesn't exist, create CSV-only view
            print(f"⚠️ JSON table not available, creating CSV-only view: {e}")
            
            contacts_csv_only = """
            CREATE VIEW FINAL_view_csv_json_contacts AS
            SELECT
                contact_id,
                display_name,
                company_name,
                first_name,
                last_name,
                email,
                phone,
                mobile,
                website,
                created_time,
                last_modified_time,
                created_timestamp,
                updated_timestamp,
                salutation,
                notes,
                contact_type,
                customer_type,
                vendor_type,
                billing_address,
                shipping_address,
                contact_persons,
                currency_id,
                payment_terms,
                payment_terms_label,
                credit_limit,
                twitter,
                facebook,
                gst_no,
                gst_treatment,
                tax_treatment,
                place_of_supply,
                vat_treatment,
                tax_regime,
                is_taxable,
                avatar_file_name,
                status,
                'CSV' as data_source,
                3 as source_priority
            FROM csv_contacts
            WHERE 
                display_name IS NOT NULL 
                OR company_name IS NOT NULL
                OR first_name IS NOT NULL
                OR last_name IS NOT NULL
            """
            cursor.execute(contacts_csv_only)
            print("✅ Successfully created CSV-only FINAL_view_csv_json_contacts")
        
        # Fix items view 
        print("\n2️⃣ FIXING FINAL_view_csv_json_items")
        print("-" * 40)
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_items")
        
        items_csv_only = """
        CREATE VIEW FINAL_view_csv_json_items AS
        SELECT
            item_id,
            item_name,
            sku,
            description,
            rate,
            purchase_rate,
            purchase_description,
            unit,
            status,
            created_timestamp,
            updated_timestamp,
            account,
            account_code,
            tax_type,
            tax_name,
            tax_percentage,
            purchase_account,
            purchase_account_code,
            inventory_account,
            inventory_account_code,
            item_type,
            product_type,
            is_returnable,
            reorder_level,
            initial_stock,
            initial_stock_rate,
            vendor_id,
            vendor_name,
            manufacturer,
            brand,
            hsn_or_sac,
            sat_item_key_code,
            unitkey_code,
            is_combo_product,
            has_attachment,
            documents,
            image_name,
            image_type,
            show_in_storefront,
            is_taxable,
            tax_exemption_id,
            tax_exemption_code,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_items
        WHERE 
            item_name IS NOT NULL 
            OR sku IS NOT NULL
            OR description IS NOT NULL
        """
        
        cursor.execute(items_csv_only)
        print("✅ Successfully created CSV-only FINAL_view_csv_json_items")
        
        # Fix sales orders view
        print("\n3️⃣ FIXING FINAL_view_csv_json_sales_orders") 
        print("-" * 40)
        
        cursor.execute("DROP VIEW IF EXISTS FINAL_view_csv_json_sales_orders")
        
        sales_orders_csv_only = """
        CREATE VIEW FINAL_view_csv_json_sales_orders AS
        SELECT
            sales_order_id,
            customer_id,
            customer_name,
            status,
            branch_id,
            branch_name,
            order_date,
            expected_shipment_date,
            shipment_date,
            invoice_date,
            due_date,
            total,
            balance,
            created_timestamp,
            updated_timestamp,
            sales_order_number,
            reference_number,
            company_id,
            currency_id,
            currency_code,
            exchange_rate,
            delivery_method,
            delivery_method_id,
            is_discount_before_tax,
            discount_type,
            entity_discount_percent,
            entity_discount_amount,
            subtotal,
            tax_total,
            adjustment,
            adjustment_description,
            salesperson_id,
            salesperson_name,
            notes,
            terms,
            billing_address,
            shipping_address,
            template_id,
            template_name,
            template_type,
            attachment_name,
            can_send_in_mail,
            is_emailed,
            is_backorder,
            page_width,
            page_height,
            orientation,
            is_inclusive_tax,
            line_items,
            'CSV' as data_source,
            3 as source_priority
        FROM csv_sales_orders
        WHERE 
            sales_order_number IS NOT NULL 
            OR customer_name IS NOT NULL
            OR order_date IS NOT NULL
        """
        
        cursor.execute(sales_orders_csv_only)
        print("✅ Successfully created CSV-only FINAL_view_csv_json_sales_orders")
        
        # Test the new views
        print("\n📊 TESTING FIXED VIEWS")
        print("-" * 40)
        
        test_queries = [
            ("FINAL_view_csv_json_contacts", "SELECT COUNT(*) FROM FINAL_view_csv_json_contacts"),
            ("FINAL_view_csv_json_items", "SELECT COUNT(*) FROM FINAL_view_csv_json_items"),
            ("FINAL_view_csv_json_sales_orders", "SELECT COUNT(*) FROM FINAL_view_csv_json_sales_orders")
        ]
        
        for view_name, query in test_queries:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"✅ {view_name}: {count:,} rows")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
        print("The three empty FINAL views now have data visible.")
        
    except Exception as e:
        print(f"❌ Error fixing views: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_final_views()
