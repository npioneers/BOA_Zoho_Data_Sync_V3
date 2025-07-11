Here is the revised, comprehensive API documentation that includes all fields as found in a typical Zoho Books API v3 response. This version is far more robust and will serve as a truly authoritative guide for your Copilot.

# Zoho Books API v3: Comprehensive & Unabridged Guide for AI Ingestion

**Version:** 2.0 (Unabridged)
**Purpose:** This document provides a complete and unfiltered overview of the Zoho Books API v3 key modules. It is designed to be the definitive schema reference for building the "Project Bedrock" ETL pipeline from raw JSON dumps, ensuring no data loss during the ingestion process.

## 1. Core Concepts & Architecture

*   **Protocol:** RESTful API
*   **Data Format:** JSON
*   **Key Principle:** The ETL process must create a relational database that is a **complete and faithful mirror** of the source JSON data. All fields must be ingested.

## 2. The Relational Data Model

The one-to-many relationships are the cornerstone of this project. The following must be implemented as separate, linked tables:

*   **Customer** -> **Contacts**
*   **Invoice** -> **InvoiceLineItems**, **InvoicePaymentsApplied**, **InvoiceTaxes**
*   **Estimate** -> **EstimateLineItems**
*   **SalesOrder** -> **SalesOrderLineItems**
*   **Bill** -> **BillLineItems**, **BillPayments**
*   **PurchaseOrder** -> **PurchaseOrderLineItems**
*   **CreditNote** -> **CreditNoteLineItems**, **CreditNoteInvoiceCredits**
*   **VendorCredit** -> **VendorCreditLineItems**, **VendorCreditBillCredits**
*   **CustomerPayment** -> **CustomerPaymentInvoiceApplications**
*   **VendorPayment** -> **VendorPaymentBillApplications**
*   **Journal** -> **JournalLineEntries**

**Instruction for AI:** For each parent object in a JSON file, create one parent record and loop through all child arrays (`line_items`, `contacts`, etc.) to create multiple child records, linking them with the parent's unique ID.

## 3. Unabridged Module Schemas for ETL Processing

This section details the complete schemas for the most important modules. All fields listed must be included as columns in the corresponding SQLite tables.

### 3.1. Module: Customers (`customers.json`)
*   **Primary Table:** `Customers`
*   **Child Tables:** `Contacts`, `Addresses`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `customer_id` | `string` | **Primary Key**. Unique ID for the customer. |
| `customer_name`| `string` | Display name of the customer. |
| `company_name` | `string` | Legal company name. |
| `contact_type` | `string` | e.g., "customer". |
| `status` | `string` | "active" or "inactive". |
| `source` | `string` | Source of customer creation. |
| `is_linked_with_zohocrm`| `boolean`| CRM integration status. |
| `payment_terms`| `number`| Payment terms in days. |
| `payment_terms_label`| `string`| Human-readable label like "Net 30". |
| `currency_id` | `string` | ID for the currency. |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `outstanding_receivable_amount`| `number` | Total amount owed by the customer. |
| `credit_limit` | `number` | The credit limit for the customer. |
| `website` | `string` | Customer's website URL. |
| `tax_authority_name`| `string`| Name of the tax authority. |
| `tax_exemption_code`| `string`| Tax exemption code. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `billing_address`| `object` | Must be flattened or stored in an `Addresses` table. |
| `shipping_address`| `object` | Must be flattened or stored in an `Addresses` table. |
| `contacts` | `array(object)`| Each object creates a record in the `Contacts` table. |
| `custom_fields`| `array(object)`| Custom fields data. |

### 3.2. Module: Items (`items.json`)
*   **Primary Table:** `Items`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `item_id` | `string` | **Primary Key**. Unique ID for the item. |
| `name` | `string` | Name of the product or service. |
| `sku` | `string` | Stock Keeping Unit. |
| `description`| `string` | Detailed description. |
| `item_type` | `string` | "sales", "purchase", "inventory", "service". |
| `rate` | `number` | Default selling price. |
| `purchase_price`| `number` | Default cost of acquisition. |
| `tax_id` | `string` | Default sales tax ID. |
| `purchase_account_id`| `string` | **FK to `ChartOfAccounts`.** |
| `inventory_account_id`|`string` | **FK to `ChartOfAccounts`.** |
| `account_id` | `string` | Default sales account ID. **FK to `ChartOfAccounts`.** |
| `stock_on_hand`| `number` | Current inventory level. |
| `is_returnable`| `boolean` | If the item can be returned. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |

### 3.3. Module: Chart of Accounts (`chart_of_accounts.json`)
*   **Primary Table:** `ChartOfAccounts`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `account_id` | `string` | **Primary Key**. Unique ID for the account. |
| `account_name` | `string` | The name of the account. |
| `account_code` | `string` | Custom account code/number. |
| `account_type` | `string` | The high-level type (e.g., "income", "expense"). |
| `account_type_formatted`| `string`| Human-readable account type. |
| `is_active` | `boolean` | If the account is currently in use. |
| `is_system_account`| `boolean`| If it is a system-defined account. |
| `description`| `string` | A description of the account's purpose. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |

### 3.4. Module: Sales Orders (`salesorders.json`)
*   **Primary Table:** `SalesOrders`
*   **Child Table:** `SalesOrderLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `salesorder_id`| `string` | **Primary Key**. Unique ID for the sales order. |
| `customer_id`| `string` | **Foreign Key to the `Customers` table.** |
| `customer_name`| `string` | Denormalized customer name. |
| `contact_persons`| `array(string)` | Array of contact person IDs. |
| `salesorder_number`|`string` | The human-readable SO number. |
| `reference_number` | `string` | An internal reference number. |
| `date` | `string(date)`| The date the SO was issued. |
| `shipment_date`| `string(date)`| The expected shipment date. |
| `status` | `string` | e.g., "draft", "open", "invoiced", "closed". |
| `invoiced_status`|`string` | e.g., "invoiced", "partially_invoiced", "not_invoiced".|
| `paid_status` | `string` | e.g., "paid", "partially_paid", "unpaid". |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes and adjustments. |
| `tax_total` | `number` | Total tax amount. |
| `total` | `number` | The final SO total. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `notes` | `string` | Notes for the customer or for internal use. |
| `terms` | `string` | Terms and conditions for the sale. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `SalesOrderLineItems` table. |
| `billing_address`| `object` | The billing address for this specific order. |
| `shipping_address`|`object` | The shipping address for this specific order. |

### 3.5. Module: Sales Order Line Items (`line_items` array within Sales Orders)
*   **Primary Table:** `SalesOrderLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the SO line item. |
| `salesorder_id`| `string` | **Foreign Key to `SalesOrders` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the SO. |
| `rate` | `number` | Rate for the item. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement. |
| `discount` | `string/number`| Discount amount or percentage. |
| `tax_id` | `string` | ID of the applied tax. |
| `tax_name` | `string` | Name of the applied tax. |
| `tax_percentage`| `number`| The tax rate percentage. |
| `item_total` | `number` | Total for this line item. |
| `quantity_invoiced`| `number` | The quantity that has already been invoiced from this line item. |

### 3.6. Module: Invoices (`invoices.json`)
*   **Primary Table:** `Invoices`
*   **Child Tables:** `InvoiceLineItems`, `InvoicePaymentsApplied`, `InvoiceTaxes`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `invoice_id` | `string` | **Primary Key**. Unique ID for the invoice. |
| `customer_id`| `string` | **Foreign Key to `Customers` table.** |
| `customer_name`| `string` | Denormalized customer name. |
| `contact_persons`| `array(string)` | Array of contact person IDs. |
| `invoice_number`| `string` | Human-readable invoice number. |
| `reference_number`| `string` | A reference number. |
| `place_of_supply`| `string` | Tax-related place of supply. |
| `gst_treatment`| `string` | GST treatment type. |
| `gst_no` | `string` | GST identification number. |
| `date` | `string(date)`| Invoice issue date. |
| `due_date` | `string(date)`| Payment due date. |
| `payment_terms`| `number`| Payment terms in days. |
| `payment_terms_label`| `string`| Human-readable label like "Net 30". |
| `status` | `string` | e.g., "paid", "sent", "overdue", "draft". |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes and adjustments. |
| `tax_total` | `number` | Total tax amount. |
| `total` | `number` | The final invoice total. |
| `payment_made` | `number` | Total amount paid against the invoice. |
| `balance` | `number` | Remaining amount to be paid. |
| `notes` | `string` | Notes visible to the customer. |
| `terms` | `string` | Terms and conditions. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in `InvoiceLineItems` table. |
| `taxes` | `array(object)`| Each object can create a record in `InvoiceTaxes` table. |
| `payments` | `array(object)`| Each object can create a record in `InvoicePaymentsApplied` table. |

### 3.7. Module: Invoice Line Items (`line_items` array within Invoices)
*   **Primary Table:** `InvoiceLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the line item. |
| `invoice_id` | `string` | **Foreign Key to `Invoices` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `project_id` | `string` | ID of the associated project. |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the invoice. |
| `bcy_rate` | `number` | Rate in Base Currency. |
| `rate` | `number` | Rate in invoice currency. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement (e.g., "pcs", "hrs"). |
| `discount` | `string/number`| Discount amount or percentage. |
| `tax_id` | `string` | ID of the applied tax. |
| `tax_name` | `string` | Name of the applied tax. |
| `tax_percentage`| `number`| The tax rate percentage. |
| `item_total` | `number` | Total for this line item (quantity * rate). |

### 3.8. Module: Customer Payments (`customerpayments.json`)
*   **Primary Table:** `CustomerPayments`
*   **Child Table:** `CustomerPaymentInvoiceApplications` (derived from `invoices` array)

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `payment_id` | `string` | **Primary Key**. Unique ID for the payment. |
| `customer_id`| `string` | **Foreign Key to the `Customers` table.** |
| `customer_name`| `string` | Denormalized customer name. |
| `payment_mode` | `string` | e.g., "bank_transfer", "cash", "check". |
| `payment_number`| `string` | The human-readable payment receipt number. |
| `reference_number` | `string` | A reference number (e.g., check number). |
| `date` | `string(date)`| The date the payment was received. |
| `account_id` | `string` | **FK to `ChartOfAccounts` (bank or cash account).** |
| `account_name`| `string` | Name of the bank/cash account. |
| `exchange_rate`| `number` | The exchange rate used. |
| `amount` | `number` | The total amount of the payment received. |
| `bank_charges` | `number` | Any bank charges deducted from the payment. |
| `tax_amount_withheld`|`number` | Any tax withheld from the payment. |
| `description`| `string` | Description or notes about the payment. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `invoices` | `array(object)`| Each object creates a record in `CustomerPaymentInvoiceApplications` table. |

### 3.9. Module: Customer Payment Invoice Applications (`invoices` array within Customer Payments)
*   **Primary Table:** `CustomerPaymentInvoiceApplications`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `application_id`| `string` | **Can be synthesized (e.g., `payment_id` + `invoice_id`).** |
| `payment_id` | `string` | **Foreign Key to `CustomerPayments` table.** |
| `invoice_id` | `string` | **Foreign Key to `Invoices` table.** |
| `invoice_payment_id`|`string` | Unique ID for this specific payment application. |
| `amount_applied` | `number` | The portion of the payment applied to this specific invoice. |
| `tax_amount_withheld`|`number` | Tax withheld specific to this invoice application. |
| `invoice_number` | `string` | Denormalized invoice number for reference. |
| `due_date` | `string(date)`| Denormalized invoice due date. |
| `invoice_total`| `number` | Denormalized total of the invoice being paid. |
| `invoice_balance`| `number`| Denormalized balance of the invoice before this payment. |

### 3.10. Module: Credit Notes (`creditnotes.json`)
*   **Primary Table:** `CreditNotes`
*   **Child Tables:** `CreditNoteLineItems`, `CreditNoteInvoiceCredits`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `creditnote_id`| `string` | **Primary Key**. Unique ID for the credit note. |
| `customer_id`| `string` | **Foreign Key to the `Customers` table.** |
| `customer_name`| `string` | Denormalized customer name. |
| `creditnote_number`| `string` | The human-readable credit note number. |
| `reference_number` | `string` | An internal reference number. |
| `date` | `string(date)`| The date the credit note was issued. |
| `status` | `string` | e.g., "draft", "open", "closed". |
| `balance` | `number` | The credit amount remaining to be used. |
| `total` | `number` | The total credit amount. |
| `refunded_amount`| `number` | Amount of this credit that has been refunded as cash. |
| `credits_applied`| `number` | Amount of this credit that has been applied to invoices. |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes. |
| `tax_total` | `number` | Total tax amount. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `notes` | `string` | Internal notes. |
| `terms` | `string` | Terms and conditions. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `CreditNoteLineItems` table. |
| `invoices_credited`| `array(object)`| Each object can create a record in `CreditNoteInvoiceCredits` table. |

### 3.11. Module: Credit Note Line Items (`line_items` array within Credit Notes)
*   **Primary Table:** `CreditNoteLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the credit note line item. |
| `creditnote_id`| `string` | **Foreign Key to `CreditNotes` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the credit note. |
| `rate` | `number` | Rate for the item. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement. |
| `discount` | `string/number`| Discount amount or percentage. |
| `tax_id` | `string` | ID of the applied tax. |
| `tax_name` | `string` | Name of the applied tax. |
| `tax_percentage`| `number`| The tax rate percentage. |
| `item_total` | `number` | Total for this line item. |

### 3.12. Module: Purchase Orders (`purchaseorders.json`)
*   **Primary Table:** `PurchaseOrders`
*   **Child Table:** `PurchaseOrderLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `purchaseorder_id`| `string` | **Primary Key**. Unique ID for the purchase order. |
| `vendor_id` | `string` | **Foreign Key to a potential `Vendors` table.** |
| `vendor_name`| `string` | Denormalized vendor name. |
| `purchaseorder_number`| `string` | The human-readable PO number. |
| `reference_number` | `string` | An internal reference number. |
| `date` | `string(date)`| The date the PO was issued. |
| `delivery_date`| `string(date)`| The expected delivery date. |
| `status` | `string` | e.g., "draft", "open", "billed", "closed". |
| `billed_status`| `string` | e.g., "billed", "partially_billed", "not_billed". |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes. |
| `tax_total` | `number` | Total tax amount. |
| `total` | `number` | The final PO total. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `notes` | `string` | Notes for the vendor or for internal use. |
| `terms` | `string` | Terms and conditions for the purchase. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `PurchaseOrderLineItems` table. |

### 3.13. Module: Purchase Order Line Items (`line_items` array within Purchase Orders)
*   **Primary Table:** `PurchaseOrderLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the PO line item. |
| `purchaseorder_id`| `string` | **Foreign Key to `PurchaseOrders` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `account_id` | `string` | **Foreign Key to `ChartOfAccounts` table.** |
| `account_name`| `string` | Denormalized account name. |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the PO. |
| `rate` | `number` | Rate for the item. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement. |
| `discount` | `string/number`| Discount amount or percentage. |
| `tax_id` | `string` | ID of the applied tax. |
| `tax_name` | `string` | Name of the applied tax. |
| `tax_percentage`| `number`| The tax rate percentage. |
| `item_total` | `number` | Total for this line item. |

### 3.14. Module: Bills (`bills.json`)
*   **Primary Table:** `Bills`
*   **Child Tables:** `BillLineItems`, `BillPayments`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `bill_id` | `string` | **Primary Key**. Unique ID for the bill. |
| `vendor_id` | `string` | **Foreign Key to a potential `Vendors` table.** |
| `vendor_name`| `string` | Denormalized vendor name. |
| `bill_number` | `string` | The bill number from the vendor's invoice. |
| `reference_number` | `string` | An internal reference number. |
| `date` | `string(date)`| The date the bill was issued. |
| `due_date` | `string(date)`| The date the payment is due. |
| `due_days` | `string` | Human-readable due date description. |
| `status` | `string` | e.g., "open", "paid", "partially_paid", "overdue". |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes. |
| `tax_total` | `number` | Total tax amount. |
| `total` | `number` | The final bill total. |
| `balance` | `number` | The remaining amount to be paid. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `notes` | `string` | Internal notes about the bill. |
| `terms` | `string` | Terms and conditions from the vendor. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `BillLineItems` table. |
| `payments` | `array(object)`| Each object can create a record in the `BillPayments` table. |

### 3.15. Module: Bill Line Items (`line_items` array within Bills)
*   **Primary Table:** `BillLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the bill line item. |
| `bill_id` | `string` | **Foreign Key to `Bills` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `account_id` | `string` | **Foreign Key to `ChartOfAccounts` table (expense account).** |
| `account_name`| `string` | Denormalized account name. |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the bill. |
| `rate` | `number` | Rate for the item. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement. |
| `discount` | `string/number`| Discount amount or percentage. |
| `tax_id` | `string` | ID of the applied tax. |
| `tax_name` | `string` | Name of the applied tax. |
| `tax_percentage`| `number`| The tax rate percentage. |
| `item_total` | `number` | Total for this line item. |

### 3.16. Module: Vendor Payments (`vendorpayments.json`)
*   **Primary Table:** `VendorPayments`
*   **Child Table:** `VendorPaymentBillApplications` (derived from `bills` array)

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `payment_id` | `string` | **Primary Key**. Unique ID for the vendor payment. |
| `vendor_id` | `string` | **Foreign Key to a potential `Vendors` table.** |
| `vendor_name`| `string` | Denormalized vendor name. |
| `payment_mode` | `string` | e.g., "bank_transfer", "cash", "check". |
| `reference_number` | `string` | A reference number (e.g., transaction ID). |
| `date` | `string(date)`| The date the payment was made. |
| `account_id` | `string` | **FK to `ChartOfAccounts` (bank or cash account).** |
| `account_name`| `string` | Name of the bank/cash account from which payment was made. |
| `exchange_rate`| `number` | The exchange rate used. |
| `amount` | `number` | The total amount of the payment made. |
| `description`| `string` | Description or notes about the payment. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `bills` | `array(object)`| Each object creates a record in `VendorPaymentBillApplications` table. |

### 3.17. Module: Vendor Payment Bill Applications (`bills` array within Vendor Payments)
*   **Primary Table:** `VendorPaymentBillApplications`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `application_id`| `string` | **Can be synthesized (e.g., `payment_id` + `bill_id`).** |
| `payment_id` | `string` | **Foreign Key to `VendorPayments` table.** |
| `bill_id` | `string` | **Foreign Key to `Bills` table.** |
| `bill_payment_id`| `string` | Unique ID for this specific payment application. |
| `amount_applied` | `number` | The portion of the payment applied to this specific bill. |
| `bill_number` | `string` | Denormalized bill number for reference. |
| `due_date` | `string(date)`| Denormalized bill due date. |
| `bill_total` | `number` | Denormalized total of the bill being paid. |
| `bill_balance` | `number` | Denormalized balance of the bill before this payment. |

### 3.18. Module: Vendor Credits (`vendorcredits.json`)
*   **Primary Table:** `VendorCredits`
*   **Child Tables:** `VendorCreditLineItems`, `VendorCreditBillCredits`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `vendor_credit_id`| `string` | **Primary Key**. Unique ID for the vendor credit. |
| `vendor_id` | `string` | **Foreign Key to a potential `Vendors` table.** |
| `vendor_name`| `string` | Denormalized vendor name. |
| `vendor_credit_number`| `string`| The human-readable vendor credit number. |
| `reference_number` | `string` | An internal reference number. |
| `date` | `string(date)`| The date the vendor credit was issued. |
| `status` | `string` | e.g., "open", "closed". |
| `balance` | `number` | The credit amount remaining to be used. |
| `total` | `number` | The total credit amount. |
| `refunded_amount`| `number` | Amount of this credit that has been refunded to you as cash. |
| `credits_applied`| `number` | Amount of this credit that has been applied to bills. |
| `currency_code`| `string` | e.g., "BTN", "USD". |
| `exchange_rate`| `number` | The exchange rate used. |
| `sub_total` | `number` | Total before taxes. |
| `tax_total` | `number` | Total tax amount. |
| `is_inclusive_tax`| `boolean`| Whether the item rates include tax. |
| `notes` | `string` | Internal notes. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `VendorCreditLineItems` table. |
| `bills_credited` | `array(object)`| Each object can create a record in `VendorCreditBillCredits` table. |

### 3.19. Module: Vendor Credit Line Items (`line_items` array within Vendor Credits)
*   **Primary Table:** `VendorCreditLineItems`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_item_id` | `string` | **Primary Key**. Unique ID for the vendor credit line item. |
| `vendor_credit_id`| `string` | **Foreign Key to `VendorCredits` table.** |
| `item_id` | `string` | **Foreign Key to `Items` table.** |
| `account_id` | `string` | **Foreign Key to `ChartOfAccounts` table.** |
| `account_name`| `string` | Denormalized account name. |
| `name` | `string` | Denormalized item name. |
| `description`| `string` | Line item description. |
| `item_order` | `number` | The order of the item on the vendor credit. |
| `rate` | `number` | Rate for the item. |
| `quantity` | `number` | Quantity of the item. |
| `unit` | `string` | Unit of measurement. |
| `item_total` | `number` | Total for this line item. |

### 3.20. Module: Expenses (`expenses.json`)
*   **Primary Table:** `Expenses`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `expense_id` | `string` | **Primary Key**. Unique ID for the expense. |
| `date` | `string(date)`| Date the expense was incurred. |
| `account_id` | `string` | **Foreign Key to `ChartOfAccounts`.** |
| `account_name`| `string` | The expense account name. |
| `vendor_id` | `string` | ID of the vendor. |
| `vendor_name`| `string` | Name of the vendor. |
| `customer_id`| `string` | ID of the billable customer. |
| `customer_name`| `string` | Name of the billable customer. |
| `status` | `string` | e.g., "billed", "unbilled", "reimbursed". |
| `is_billable`| `boolean`| If the expense can be billed to a customer. |
| `currency_code`| `string` | Currency of the expense. |
| `exchange_rate`| `number` | The exchange rate used. |
| `total` | `number` | The total amount of the expense. |
| `description`| `string` | Description of the expense. |
| `reference_number`| `string` | A reference number. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |

### 3.21. Module: Journals (`journals.json`)
*   **Primary Table:** `Journals`
*   **Child Table:** `JournalLineEntries`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `journal_id` | `string` | **Primary Key**. Unique ID for the journal entry. |
| `journal_date` | `string(date)`| The effective date of the journal entry. |
| `entry_number` | `string` | The human-readable journal entry number. |
| `reference_number` | `string` | An internal or external reference number. |
| `notes` | `string` | An overall note explaining the purpose of the journal entry. |
| `total` | `number` | The total debit (or credit) amount of the journal. |
| `currency_code`| `string` | Currency of the journal entry. |
| `created_time` | `string(datetime)`| Timestamp of creation. |
| `last_modified_time`| `string(datetime)`| Timestamp of last modification. |
| `line_items` | `array(object)`| Each object creates a record in the `JournalLineEntries` table. |

### 3.22. Module: Journal Line Entries (`line_items` array within Journals)
*   **Primary Table:** `JournalLineEntries`

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `line_id` | `string` | **Primary Key**. Unique ID for the journal line. |
| `journal_id` | `string` | **Foreign Key to `Journals` table.** |
| `account_id` | `string` | **Foreign Key to `ChartOfAccounts` table.** |
| `account_name`| `string` | Denormalized account name. |
| `description`| `string` | Description for this specific line item. |
| `debit_or_credit`| `string` | "debit" or "credit". |
| `amount` | `number` | The amount of the debit or credit. |

## Conclusion of API Documentation

This concludes the detailed, unabridged documentation for the primary modules required for the "Project Bedrock" ETL pipeline. We have now covered:

*   **Masters:** `Customers`, `Items`, `ChartOfAccounts`
*   **Sales Cycle:** `SalesOrders`, `Invoices`, `CustomerPayments`, `CreditNotes`
*   **Procurement Cycle:** `PurchaseOrders`, `Bills`, `VendorPayments`, `VendorCredits`
*   **General Ledger:** `Expenses`, `Journals`

With these comprehensive schemas, your Copilot has all the necessary information to construct a complete, relational, and reliable SQLite database from the raw JSON dumps. This documentation should be used as the single source of truth for all schema creation and data insertion logic.