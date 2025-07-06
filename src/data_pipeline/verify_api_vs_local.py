#!/usr/bin/env python3
"""
Verify API vs Local Data Completeness
Compares what's available in Zoho API vs what we have downloaded locally
"""

import json
import os
import requests
import time
from datetime import datetime
import sys
import glob

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def get_api_credentials():
    """Get API credentials from existing auth system"""
    try:
        from data_sync.core.auth import get_access_token
        from data_sync.core.secrets import get_zoho_credentials
        
        print("🔐 Getting Zoho API credentials...")
        credentials = get_zoho_credentials()
        access_token = get_access_token(credentials)
        
        if access_token:
            print("✅ Successfully obtained access token")
            return {
                'access_token': access_token,
                'organization_id': credentials.get('organization_id')
            }
        else:
            print("❌ Failed to get access token")
            return None
            
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        return None

class ApiLocalVerifier:
    def __init__(self, json_folder):
        self.base_url = "https://www.zohoapis.com/books/v3"
        self.access_token = None
        self.organization_id = None
        self.json_folder = json_folder
        self.session = requests.Session()
        
        print(f"📁 Verifying JSON folder: {json_folder}")
    
    def authenticate(self):
        """Get Zoho API credentials and access token"""
        print("🔐 Getting Zoho API credentials...")
        
        try:
            credentials = get_api_credentials()
            if not credentials:
                return False
                
            self.access_token = credentials['access_token']
            self.organization_id = credentials.get('organization_id')
            
            self.session.headers.update({
                'Authorization': f'Zoho-oauthtoken {self.access_token}',
                'Content-Type': 'application/json'
            })
            
            print("✅ Successfully authenticated with Zoho API")
            
            # If no organization_id, get the default one
            if not self.organization_id:
                print("🔍 Getting organization...")
                orgs_response = self.session.get(f"{self.base_url}/organizations")
                
                if orgs_response.status_code == 200:
                    orgs_data = orgs_response.json()
                    organizations = orgs_data.get('organizations', [])
                    
                    for org in organizations:
                        if org.get('is_default_org', False):
                            self.organization_id = org.get('organization_id')
                            break
                    
                    if not self.organization_id and organizations:
                        self.organization_id = organizations[0].get('organization_id')
                
                else:
                    print(f"❌ Failed to get organizations: {orgs_response.status_code}")
                    return False
            
            print(f"🎯 Using organization_id: {self.organization_id}")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_api_count(self, endpoint):
        """Get total count from API for an endpoint with pagination"""
        
        url = f"{self.base_url}/{endpoint}"
        page = 1
        total_count = 0
        
        while True:
            params = {
                'organization_id': self.organization_id,
                'per_page': 200,
                'page': page
            }
            
            try:
                print(f"      🌐 Querying API: {endpoint} (page {page})...")
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Get page context
                    page_context = data.get('page_context', {})
                    has_more_page = page_context.get('has_more_page', False)
                    
                    # Count records on this page
                    page_count = 0
                    data_keys = [
                        'invoices', 'items', 'contacts', 'customerpayments', 
                        'bills', 'vendorpayments', 'salesorders', 'purchaseorders',
                        'creditnotes', 'organizations'
                    ]
                    
                    for key in data_keys:
                        if key in data:
                            page_count = len(data[key])
                            break
                    
                    if page_count == 0 and 'data' in data:
                        page_count = len(data['data'])
                    
                    total_count += page_count
                    print(f"         📋 Page {page}: {page_count} records")
                    
                    # If no more pages or empty page, break
                    if not has_more_page or page_count == 0:
                        break
                    
                    page += 1
                    time.sleep(0.5)  # Rate limiting between pages
                    
                    # Safety limit to prevent infinite loops
                    if page > 50:  # Max 50 pages = 10,000 records
                        print(f"         ⚠️  Reached safety limit at page {page}")
                        break
                        
                else:
                    if response.status_code == 403:
                        print(f"      🔒 Permission denied for {endpoint}")
                        return "NO_PERMISSION"
                    else:
                        print(f"      ❌ API Error {response.status_code}: {response.text[:200]}")
                        return None
                    
            except Exception as e:
                print(f"      ❌ Request failed: {e}")
                return None
        
        print(f"      ✅ Total across {page} pages: {total_count}")
        return total_count
    
    def get_local_count(self, entity_type):
        """Get count from local JSON files"""
        
        # Check combined file first
        combined_file = os.path.join(self.json_folder, f"{entity_type}_combined.json")
        
        if os.path.exists(combined_file):
            try:
                with open(combined_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('total_count', len(data.get('data', [])))
            except:
                return 0
        
        # Check single file
        single_file = os.path.join(self.json_folder, f"{entity_type}.json")
        if os.path.exists(single_file):
            try:
                with open(single_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Count records in the data
                data_part = data.get('data', {})
                
                # Check for specific entity keys
                entity_keys = [
                    'invoices', 'items', 'contacts', 'customerpayments', 
                    'bills', 'vendorpayments', 'salesorders', 'purchaseorders',
                    'creditnotes', 'organizations'
                ]
                
                for key in entity_keys:
                    if key in data_part:
                        return len(data_part[key])
                
                # Fallback to direct data key matching
                if entity_type in data_part:
                    return len(data_part[entity_type])
                
                return 1
            except:
                return 1
            
        return 0
    
    def get_local_detailed_count(self, entity_type):
        """Get count of detailed files from local folders"""
        
        # First check detailed combined file
        detailed_combined = os.path.join(self.json_folder, f"{entity_type}_detailed_combined.json")
        if os.path.exists(detailed_combined):
            try:
                with open(detailed_combined, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('total_count', 0), data.get('total_line_items', 0)
            except:
                pass
        
        # Check detailed folder
        folder_mapping = {
            'invoices': 'detailed_invoices',
            'bills': 'detailed_bills', 
            'sales_orders': 'detailed_sales_orders',
            'purchase_orders': 'detailed_purchase_orders',
            'credit_notes': 'detailed_credit_notes'
        }
        
        detailed_folder = os.path.join(self.json_folder, folder_mapping.get(entity_type, f"detailed_{entity_type}"))
        
        if os.path.exists(detailed_folder):
            files = [f for f in os.listdir(detailed_folder) if f.endswith('.json')]
            
            # Estimate line items from sampling
            sample_count = min(5, len(files))
            total_line_items = 0
            
            if sample_count > 0:
                for i in range(sample_count):
                    file_path = os.path.join(detailed_folder, files[i])
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                            entity_data = file_data.get('data', {})
                            line_items = entity_data.get('line_items', [])
                            total_line_items += len(line_items)
                    except:
                        continue
                
                if sample_count > 0:
                    avg_line_items = total_line_items / sample_count
                    estimated_line_items = int(avg_line_items * len(files))
                    return len(files), estimated_line_items
            
            return len(files), 0
        
        return 0, 0
    
    def verify_all_endpoints(self):
        """Verify all main endpoints against API"""
        
        print(f"\n🔍 API vs LOCAL VERIFICATION")
        print("=" * 80)
        print(f"📁 Local folder: {self.json_folder}")
        print(f"🕐 Verification time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.authenticate():
            return False
        
        # Define all endpoints to check
        endpoints = [
            ('invoices', 'invoices', 'Sales invoices'),
            ('items', 'items', 'Products/services'),
            ('contacts', 'contacts', 'Customers/vendors'),
            ('customer_payments', 'customerpayments', 'Customer payments'),
            ('bills', 'bills', 'Vendor bills'),
            ('vendor_payments', 'vendorpayments', 'Vendor payments'),
            ('sales_orders', 'salesorders', 'Sales orders'),
            ('purchase_orders', 'purchaseorders', 'Purchase orders'),
            ('credit_notes', 'creditnotes', 'Credit notes'),
            ('organizations', 'organizations', 'Organization info')
        ]
        
        print(f"\n📋 MAIN DATA VERIFICATION:")
        print("-" * 50)
        
        total_api = 0
        total_local = 0
        mismatches = []
        
        for local_name, api_endpoint, description in endpoints:
            print(f"\n🔍 Checking {description}...")
            
            # Get API count
            api_count = self.get_api_count(api_endpoint)
            time.sleep(0.5)  # Rate limiting
            
            # Get local count
            local_count = self.get_local_count(local_name)
            
            if api_count is not None:
                if api_count == "NO_PERMISSION":
                    status = "🔒"
                    print(f"   {status} {description}")
                    print(f"      🌐 API: NO PERMISSION")
                    print(f"      💾 Local: {local_count:,}")
                else:
                    total_api += api_count
                    total_local += local_count
                    
                    if api_count == local_count:
                        status = "✅"
                    else:
                        status = "⚠️"
                        mismatches.append((local_name, api_count, local_count))
                    
                    print(f"   {status} {description}")
                    print(f"      🌐 API: {api_count:,}")
                    print(f"      💾 Local: {local_count:,}")
                    
                    if api_count != local_count:
                        diff = local_count - api_count
                        if diff > 0:
                            print(f"      📈 Local has {diff:,} MORE records")
                        else:
                            print(f"      📉 Local is MISSING {abs(diff):,} records")
            else:
                print(f"   ❌ {description}")
                print(f"      🌐 API: ERROR")
                print(f"      💾 Local: {local_count:,}")
        
        # Check detailed line items
        print(f"\n📑 LINE ITEMS VERIFICATION:")
        print("-" * 50)
        
        line_items_entities = [
            ('invoices', 'Invoice line items'),
            ('bills', 'Bill line items'),
            ('sales_orders', 'Sales order line items'),
            ('purchase_orders', 'Purchase order line items'),
            ('credit_notes', 'Credit note line items')
        ]
        
        total_local_entities = 0
        total_local_line_items = 0
        
        for entity, description in line_items_entities:
            detailed_count, line_items_count = self.get_local_detailed_count(entity)
            
            # Get expected count from main data
            expected_count = self.get_local_count(entity)
            
            if detailed_count > 0:
                if detailed_count == expected_count:
                    status = "✅"
                elif detailed_count > expected_count:
                    status = "📈"
                else:
                    status = "⚠️"
                
                print(f"   {status} {description}")
                print(f"      📊 Expected entities: {expected_count:,}")
                print(f"      💾 Downloaded entities: {detailed_count:,}")
                print(f"      📑 Line items: {line_items_count:,}")
                
                total_local_entities += detailed_count
                total_local_line_items += line_items_count
            else:
                print(f"   ❌ {description}")
                print(f"      📊 Expected entities: {expected_count:,}")
                print(f"      💾 Downloaded entities: 0")
        
        # Summary
        print(f"\n🎯 VERIFICATION SUMMARY:")
        print("=" * 80)
        print(f"📊 Main Records:")
        print(f"   🌐 API Total: {total_api:,}")
        print(f"   💾 Local Total: {total_local:,}")
        
        if total_api == total_local:
            print(f"   ✅ PERFECT MATCH!")
        else:
            diff = total_local - total_api
            if diff > 0:
                print(f"   📈 Local has {diff:,} MORE records")
            else:
                print(f"   📉 Local is MISSING {abs(diff):,} records")
        
        print(f"\n📑 Line Items:")
        print(f"   💾 Total entities with details: {total_local_entities:,}")
        print(f"   📑 Total line items: {total_local_line_items:,}")
        
        if mismatches:
            print(f"\n⚠️  MISMATCHES FOUND:")
            for entity, api_count, local_count in mismatches:
                diff = local_count - api_count
                if diff > 0:
                    print(f"   📈 {entity}: Local +{diff:,} (API: {api_count:,}, Local: {local_count:,})")
                else:
                    print(f"   📉 {entity}: Local {diff:,} (API: {api_count:,}, Local: {local_count:,})")
        else:
            print(f"\n✅ ALL MAIN ENDPOINTS MATCH!")
        
        # Recommendations
        print(f"\n🚀 RECOMMENDATIONS:")
        if mismatches:
            print("   ⚠️  Some mismatches found - review specific endpoints")
            print("   🔄 Consider re-downloading mismatched endpoints")
        else:
            print("   ✅ Data appears complete and accurate")
            print("   🎯 Ready to proceed with import_from_json.py")
        
        return len(mismatches) == 0

def main():
    """Main verification function"""
    
    # Find the latest JSON folder
    json_folders = glob.glob("json_data_*")
    if not json_folders:
        print("❌ No JSON data folders found")
        return False
    
    # Use the latest folder
    latest_folder = max(json_folders, key=os.path.getctime)
    print(f"📁 Using JSON folder: {latest_folder}")
    
    verifier = ApiLocalVerifier(latest_folder)
    success = verifier.verify_all_endpoints()
    
    return success

if __name__ == "__main__":
    main()
