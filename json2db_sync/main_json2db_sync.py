"""
JSON2DB Sync Main Wrapper
User-friendly interface with menus for JSON to Database synchronization.
Provides interactive menus and calls runner functions.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Handle imports for both standalone and module usage
try:
    from .runner_json2db_sync import JSON2DBSyncRunner
    from .config import get_config
except ImportError:
    from runner_json2db_sync import JSON2DBSyncRunner
    from config import get_config


class JSON2DBSyncWrapper:
    """User-friendly wrapper for JSON2DB synchronization operations"""
    
    def __init__(self):
        self.runner = JSON2DBSyncRunner()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, result: dict, operation: str = "Operation"):
        """Print formatted operation result"""
        if result.get("success"):
            print(f"\n✅ {operation} completed successfully!")
            
            # Print statistics if available
            stats = result.get("statistics", {})
            if stats:
                print("\n📊 Statistics:")
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
            
            # Print completion time
            completed_at = result.get("completed_at")
            if completed_at:
                print(f"   • Completed at: {completed_at}")
                
        else:
            print(f"\n❌ {operation} failed!")
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            errors = result.get("errors", [])
            if errors:
                print("\n   Detailed errors:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"   • {error}")
                if len(errors) > 5:
                    print(f"   ... and {len(errors) - 5} more errors")

    def get_user_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()

    def confirm_action(self, message: str) -> bool:
        """Get user confirmation"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")

    def pause(self):
        """Pause for user to read output"""
        input("\nPress Enter to continue...")

    def show_main_menu(self):
        """Display main menu and handle selection"""
        while True:
            self.clear_screen()
            self.print_header("JSON2DB Sync - Main Menu")
            
            print("\n🔧 Available Operations:")
            print("   1. Analyze JSON Files")
            print("   2. Populate Tables with Data")
            print("   3. Verify Tables")
            print("   4. Generate Summary Report")
            print("   5. Full Sync Workflow")
            print("   6. Advanced Options")
            print("   0. Exit")
            
            choice = input("\nSelect an option (0-6): ").strip()
            
            if choice == '1':
                self.handle_json_analysis()
            elif choice == '2':
                self.handle_data_population()
            elif choice == '3':
                self.handle_table_verification()
            elif choice == '4':
                self.handle_summary_report()
            elif choice == '5':
                self.handle_full_workflow()
            elif choice == '6':
                self.show_advanced_menu()
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 0-6.")
                self.pause()

    def show_advanced_menu(self):
        """Display advanced options menu"""
        while True:
            self.clear_screen()
            self.print_header("JSON2DB Sync - Advanced Options")
            
            print("\n⚙️ Advanced Operations:")
            print("   1. Recreate JSON Tables (Recommended)")
            print("   2. Create All Tables (Full Creation)")
            print("   3. Generate Table Schemas Only")
            print("   4. Custom Workflow Configuration")
            print("   5. Check Current Configuration")
            print("   0. Back to Main Menu")
            
            choice = input("\nSelect an option (0-5): ").strip()
            
            if choice == '1':
                self.handle_table_recreation()
            elif choice == '2':
                self.handle_full_table_creation()
            elif choice == '3':
                self.handle_schema_generation()
            elif choice == '4':
                self.handle_custom_workflow()
            elif choice == '5':
                self.show_configuration()
            elif choice == '0':
                break
            else:
                print("\n❌ Invalid choice. Please select 0-5.")
                self.pause()

    def handle_json_analysis(self):
        """Handle JSON file analysis"""
        self.clear_screen()
        self.print_header("JSON File Analysis")
        
        print("\n📁 This will analyze JSON files from sync sessions to understand their structure.")
        print("💡 System is configured to always use session-based data from api_sync/data/sync_sessions")
        
        # Get JSON directory from configuration (session-based only)
        config = get_config()
        default_json_dir = config.get_api_sync_path()
        
        print(f"\n📁 Default sync sessions path: {default_json_dir}")
        
        json_dir = self.get_user_input("Sync sessions directory", default_json_dir)
        
        if not Path(json_dir).exists():
            print(f"\n❌ Directory not found: {json_dir}")
            self.pause()
            return
        
        print(f"\n🔍 Analyzing JSON files in: {json_dir}")
        result = self.runner.analyze_json_files(json_dir)
        
        if result.get("success"):
            print("\n✅ JSON Analysis completed successfully!")
            
            schema_analysis = result.get("schema_analysis", {})
            if schema_analysis:
                self._display_json_analysis_table(schema_analysis, json_dir)
            else:
                print("\n📋 No JSON files found for analysis.")
        else:
            self.print_result(result, "JSON Analysis")
        
        self.pause()
    
    def _display_json_analysis_table(self, schema_analysis: dict, json_dir: str):
        """Display comprehensive JSON analysis table"""
        print(f"\n� JSON File Analysis Report")
        print("=" * 80)
        
        # Sort tables by category and name
        main_entities = {}
        line_item_tables = {}
        
        for table_name, table_info in schema_analysis.items():
            if '_line_items' in table_name or 'line_items' in table_name:
                line_item_tables[table_name] = table_info
            else:
                main_entities[table_name] = table_info
        
        # Table header
        print(f"{'Table Name':<28} {'Records':<10} {'Columns':<8} {'JSON File':<25} {'Status'}")
        print("-" * 80)
        
        total_records = 0
        total_tables = 0
        main_entities_count = 0
        line_items_count = 0
        
        # Display main entities first
        if main_entities:
            print("📋 MAIN ENTITIES:")
            for table_name in sorted(main_entities.keys()):
                table_info = main_entities[table_name]
                analysis = table_info.get('analysis', {})
                record_count = analysis.get('record_count', 0)
                column_count = len(analysis.get('columns', {}))
                json_file = table_info.get('json_file', 'Unknown')
                
                # Status with emoji
                if record_count > 0:
                    status = "✅ Has Data"
                else:
                    status = "⚠️  Empty"
                
                print(f"{table_name:<28} {record_count:<10,} {column_count:<8} {json_file:<25} {status}")
                
                total_records += record_count
                total_tables += 1
                main_entities_count += 1
        
        # Display line item tables
        if line_item_tables:
            if main_entities:
                print()
            print("🔗 LINE ITEM TABLES:")
            for table_name in sorted(line_item_tables.keys()):
                table_info = line_item_tables[table_name]
                analysis = table_info.get('analysis', {})
                record_count = analysis.get('record_count', 0)
                column_count = len(analysis.get('columns', {}))
                json_file = table_info.get('json_file', 'Unknown')
                
                # Status with emoji
                if record_count > 0:
                    status = "✅ Has Data"
                else:
                    status = "⚠️  Empty"
                
                print(f"{table_name:<28} {record_count:<10,} {column_count:<8} {json_file:<25} {status}")
                
                total_records += record_count
                total_tables += 1
                line_items_count += 1
        
        # Summary section
        print("=" * 80)
        print("📈 SUMMARY:")
        print(f"   • Total Tables Found: {total_tables}")
        print(f"   • Main Entities: {main_entities_count}")
        print(f"   • Line Item Tables: {line_items_count}")
        print(f"   • Total Records: {total_records:,}")
        print(f"   • Analysis Source: {json_dir}")
        
        # Show tables with and without data
        tables_with_data = len([t for t in schema_analysis.values() 
                              if t.get('analysis', {}).get('record_count', 0) > 0])
        empty_tables = total_tables - tables_with_data
        
        if empty_tables > 0:
            print(f"   • Tables with Data: {tables_with_data}")
            print(f"   • Empty Tables: {empty_tables}")
        
        print("=" * 80)
        
        # Date Range Analysis Table
        self._display_date_range_table(schema_analysis)
    
    def _display_date_range_table(self, schema_analysis: dict):
        """Display date range information for JSON files"""
        print(f"\n📅 Date Range Analysis")
        print("=" * 90)
        
        # Filter files that have date information
        files_with_dates = {}
        files_without_dates = []
        
        for table_name, table_info in schema_analysis.items():
            analysis = table_info.get('analysis', {})
            date_range = analysis.get('date_range', {})
            
            if date_range.get('earliest_date') and date_range.get('latest_date'):
                files_with_dates[table_name] = {
                    'table_info': table_info,
                    'date_range': date_range
                }
            else:
                files_without_dates.append(table_name)
        
        if files_with_dates:
            # Table header
            print(f"{'Table Name':<28} {'Date Field':<18} {'From Date':<12} {'To Date':<12} {'Records':<8} {'With Dates'}")
            print("-" * 90)
            
            # Sort by earliest date
            sorted_files = sorted(files_with_dates.items(), 
                                key=lambda x: x[1]['date_range']['earliest_date'])
            
            for table_name, info in sorted_files:
                date_range = info['date_range']
                analysis = info['table_info'].get('analysis', {})
                
                date_field = date_range.get('date_field', 'Unknown')
                earliest = date_range.get('earliest_date', 'N/A')
                latest = date_range.get('latest_date', 'N/A')
                total_records = date_range.get('total_records', 0)
                records_with_dates = date_range.get('records_with_dates', 0)
                
                # Format date field name
                if len(date_field) > 17:
                    date_field = date_field[:14] + "..."
                
                print(f"{table_name:<28} {date_field:<18} {earliest:<12} {latest:<12} {total_records:<8,} {records_with_dates:,}")
        
        # Show files without date information
        if files_without_dates:
            print(f"\n📋 FILES WITHOUT DATE INFORMATION:")
            for table_name in sorted(files_without_dates):
                analysis = schema_analysis[table_name].get('analysis', {})
                record_count = analysis.get('record_count', 0)
                print(f"   • {table_name}: {record_count:,} records (no date fields found)")
        
        print("=" * 90)

    def handle_table_recreation(self):
        """Handle JSON table recreation"""
        self.clear_screen()
        self.print_header("Recreate JSON Tables")
        
        print("\n🔄 This will recreate JSON tables in the existing database.")
        print("   • Preserves database file and other tables")
        print("   • Recommended for regular operations")
        
        # Get database path from configuration
        config = get_config()
        db_path = config.get_database_path()
        print(f"📁 Database path: {db_path}")
        
        print(f"\n🔄 Recreating JSON tables in: {db_path}")
        result = self.runner.recreate_json_tables(db_path)
        
        self.print_result(result, "Table Recreation")
        self.pause()

    def handle_data_population(self):
        """Handle data population"""
        self.clear_screen()
        self.print_header("Populate Tables with Data")
        
        print("\n📊 This will populate JSON tables with data from sync sessions.")
        print("💡 System is configured to always use session-based data from api_sync/data/sync_sessions")
        print("\n⚠️  WARNING: This operation will:")
        print("   • CLEAR existing data in JSON tables")
        print("   • Populate tables with fresh data from sessions")
        print("   • Use 30-day cutoff filter automatically")
        print("   • Apply duplicate prevention measures")
        
        # Get paths from configuration (session-based only)
        config = get_config()
        db_path = config.get_database_path()
        json_dir = config.get_api_sync_path()
        
        print(f"\n📁 Database path: {db_path}")
        print(f"📁 Sync sessions path: {json_dir}")
        
        # Check if paths exist
        if not Path(db_path).exists():
            print(f"\n❌ Database file not found: {db_path}")
            self.pause()
            return
        
        if not Path(json_dir).exists():
            print(f"\n❌ JSON directory not found: {json_dir}")
            self.pause()
            return
        
        # Add confirmation before proceeding
        if not self.confirm_action("\n⚠️  Proceed with table clearing and data population?"):
            print("📋 Operation cancelled by user.")
            self.pause()
            return
        
        # Use default 30-day cutoff (no user confirmation)
        cutoff_days = 30
        print(f"🗓️  Using default 30-day cutoff filter")
        
        print(f"\n📊 Populating tables with data from last {cutoff_days} days...")
        result = self.runner.populate_tables(db_path, json_dir, cutoff_days)
        
        self.print_result(result, "Data Population")
        self.pause()

    def handle_table_verification(self):
        """Handle table verification"""
        self.clear_screen()
        self.print_header("Verify Tables")
        
        print("\n✅ This will verify the structure and data of JSON tables.")
        
        config = get_config()
        default_db_path = config.get_database_path()
        db_path = self.get_user_input("Database file path", default_db_path)
        
        if not Path(db_path).exists():
            print(f"\n❌ Database file not found: {db_path}")
            self.pause()
            return
        
        print(f"\n✅ Verifying tables in: {db_path}")
        result = self.runner.verify_tables(db_path)
        
        if result.get("success") and "verification_result" in result:
            verification_result = result["verification_result"]
            
            if "summary_report" in verification_result:
                summary = verification_result["summary_report"]
                
                if "error" in summary:
                    print(f"\n❌ Verification Error: {summary['error']}")
                else:
                    self._display_table_summary_report(summary)
            else:
                self.print_result(result, "Table Verification")
        else:
            self.print_result(result, "Table Verification")
        
        self.pause()

    def _display_table_summary_report(self, summary: Dict[str, Any]):
        """Display the table summary report in a formatted table"""
        print(f"\n📊 DATABASE SUMMARY REPORT")
        print("=" * 105)
        
        # Display overview statistics
        print(f"📁 Total Tables: {summary.get('total_tables', 0)}")
        print(f"📊 Populated Tables: {summary.get('populated_tables', 0)}/{summary.get('total_tables', 0)}")
        print(f"📈 Total Records: {summary.get('total_records', 0):,}")
        print(f"🕒 Generated: {summary.get('generated_at', 'Unknown')[:19]}")
        print("=" * 105)
        
        # Display detailed table information
        table_details = summary.get('table_details', [])
        if table_details:
            print(f"\n📋 DETAILED TABLE ANALYSIS")
            print("-" * 105)
            print(f"{'Table Name':<30} {'Row Count':<12} {'Oldest Data':<20} {'Latest Data':<20} {'Last Sync':<20}")
            print("-" * 105)
            
            for table in table_details:
                # Format table name with proper truncation
                table_name = table.get('table_name', 'Unknown')
                if len(table_name) > 28:  # Leave room for emoji + space
                    table_name = table_name[:25] + "..."
                
                # Format row count with comma separation
                row_count = f"{table.get('row_count', 0):,}"
                
                # Format dates with consistent truncation
                oldest_date = str(table.get('oldest_date', 'N/A'))
                if len(oldest_date) > 19:
                    oldest_date = oldest_date[:19]
                
                latest_date = str(table.get('latest_date', 'N/A'))
                if len(latest_date) > 19:
                    latest_date = latest_date[:19]
                
                last_sync = str(table.get('last_sync_timestamp', 'N/A'))
                if len(last_sync) > 19:
                    last_sync = last_sync[:19]
                
                # Add emoji for populated vs empty tables
                status_emoji = "✅" if table.get('row_count', 0) > 0 else "❌"
                table_display = f"{status_emoji} {table_name}"
                
                print(f"{table_display:<30} {row_count:<12} {oldest_date:<20} {latest_date:<20} {last_sync:<20}")
            
            print("-" * 105)
            
            # Display summary statistics
            empty_tables = [t for t in table_details if t.get('row_count', 0) == 0]
            if empty_tables:
                print(f"\n⚠️  Empty Tables ({len(empty_tables)}):")
                for table in empty_tables:
                    print(f"   • {table.get('table_name', 'Unknown')}")
            
            # Display top tables by record count
            top_tables = sorted(table_details, key=lambda x: x.get('row_count', 0), reverse=True)[:5]
            if any(t.get('row_count', 0) > 0 for t in top_tables):
                print(f"\n🏆 Top Tables by Record Count:")
                for i, table in enumerate(top_tables[:5], 1):
                    if table.get('row_count', 0) > 0:
                        print(f"   {i}. {table.get('table_name', 'Unknown')}: {table.get('row_count', 0):,} records")
        
        print(f"\n✅ Table Verification completed successfully!")
        print("=" * 105)
        
        # Pause to allow user to review the report
        input("\n📋 Press Enter to continue...")

    def handle_summary_report(self):
        """Handle summary report generation"""
        self.clear_screen()
        self.print_header("Generate Summary Report")
        
        print("\n📋 This will generate a comprehensive summary report.")
        
        config = get_config()
        db_path = config.get_database_path()
        print(f"📁 Database path: {db_path}")
        
        if not Path(db_path).exists():
            print(f"\n❌ Database file not found: {db_path}")
            self.pause()
            return
        
        print(f"\n📋 Generating summary report for: {db_path}")
        result = self.runner.generate_summary_report(db_path)
        
        self.print_result(result, "Summary Report")
        
        if result.get("success"):
            report = result.get("report", {})
            if report:
                print("\n📊 Quick Summary:")
                
                # Extract data from the comprehensive report structure
                db_info = report.get("database_info", {})
                summary_stats = report.get("summary_statistics", {})
                
                total_tables = db_info.get("total_tables", "N/A")
                total_json_records = summary_stats.get("total_json_records", 0)
                total_csv_records = summary_stats.get("total_csv_records", 0)
                total_records = total_json_records + total_csv_records if isinstance(total_json_records, int) and isinstance(total_csv_records, int) else "N/A"
                
                json_tables_populated = summary_stats.get("json_tables_populated", "N/A")
                db_size = db_info.get("database_size_mb", "N/A")
                
                print(f"   • Total tables: {total_tables}")
                print(f"   • Total records: {total_records:,}" if isinstance(total_records, int) else f"   • Total records: {total_records}")
                print(f"   • JSON tables populated: {json_tables_populated}")
                print(f"   • Database size: {db_size} MB")
        
        self.pause()

    def handle_full_workflow(self):
        """Handle full sync workflow"""
        self.clear_screen()
        self.print_header("Full Sync Workflow")
        
        print("\n🚀 This will execute the complete JSON2DB sync workflow:")
        print("   1. Analyze JSON files")
        print("   2. Recreate JSON tables")
        print("   3. Populate tables with data")
        print("   4. Verify tables")
        print("   5. Generate summary report")
        
        # Get configuration from config system (session-based only)
        config = get_config()
        default_db_path = config.get_database_path()
        default_json_dir = config.get_api_sync_path()
        
        db_path = self.get_user_input("Database file path", default_db_path)
        json_dir = self.get_user_input("JSON files directory", default_json_dir)
        
        # Check paths
        if not Path(json_dir).exists():
            print(f"\n❌ JSON directory not found: {json_dir}")
            self.pause()
            return
        
        # Workflow options
        skip_tables = self.confirm_action("\nSkip table recreation (use existing tables)?")
        
        use_cutoff = self.confirm_action("Use date cutoff filtering?")
        cutoff_days = None
        
        if use_cutoff:
            while True:
                try:
                    cutoff_input = self.get_user_input("Number of days back to include", "30")
                    cutoff_days = int(cutoff_input)
                    if cutoff_days > 0:
                        break
                    else:
                        print("Please enter a positive number")
                except ValueError:
                    print("Please enter a valid number")
        
        if not self.confirm_action("\nProceed with full workflow?"):
            return
        
        print(f"\n🚀 Starting full sync workflow...")
        result = self.runner.full_sync_workflow(db_path, json_dir, cutoff_days, skip_tables)
        
        self.print_result(result, "Full Sync Workflow")
        
        if result.get("success"):
            steps_completed = result.get("steps_completed", [])
            print(f"\n✅ Completed {len(steps_completed)} workflow steps:")
            for step in steps_completed:
                print(f"   • {step.replace('_', ' ').title()}")
        
        self.pause()

    def handle_full_table_creation(self):
        """Handle full table creation (advanced)"""
        self.clear_screen()
        self.print_header("Create All Tables (Advanced)")
        
        print("\n⚠️  WARNING: This will create ALL tables in the database.")
        print("   • Use only for new/empty databases")
        print("   • May affect existing data")
        
        if not self.confirm_action("\nThis is a potentially destructive operation. Continue?"):
            return
        
        config = get_config()
        default_db_path = config.get_database_path()
        db_path = self.get_user_input("Database file path", default_db_path)
        
        if not self.confirm_action(f"\nCreate all tables in {db_path}?"):
            return
        
        print(f"\n🏗️ Creating all tables in: {db_path}")
        result = self.runner.create_all_tables(db_path)
        
        self.print_result(result, "Full Table Creation")
        self.pause()

    def handle_schema_generation(self):
        """Handle schema generation only"""
        self.clear_screen()
        self.print_header("Generate Table Schemas")
        
        print("\n📝 This will generate SQL schemas without creating tables.")
        
        config = get_config()
        default_json_dir = config.get_api_sync_path()
        json_dir = self.get_user_input("JSON files directory", default_json_dir)
        
        if not Path(json_dir).exists():
            print(f"\n❌ Directory not found: {json_dir}")
            self.pause()
            return
        
        print(f"\n📝 Generating schemas from: {json_dir}")
        result = self.runner.generate_table_schemas(json_dir)
        
        self.print_result(result, "Schema Generation")
        
        if result.get("success"):
            table_sql = result.get("table_sql", {})
            index_sql = result.get("index_sql", {})
            print(f"\n📊 Generated:")
            print(f"   • Table schemas: {len(table_sql)}")
            print(f"   • Index schemas: {len(index_sql)}")
        
        self.pause()

    def handle_custom_workflow(self):
        """Handle custom workflow configuration"""
        self.clear_screen()
        self.print_header("Custom Workflow Configuration")
        
        print("\n⚙️ Configure a custom workflow with specific steps.")
        print("   You can choose which operations to include.")
        
        # Step selection
        steps = {
            "analysis": self.confirm_action("Include JSON analysis?"),
            "recreation": self.confirm_action("Include table recreation?"),
            "population": self.confirm_action("Include data population?"),
            "verification": self.confirm_action("Include table verification?"),
            "summary": self.confirm_action("Include summary report?")
        }
        
        if not any(steps.values()):
            print("\n❌ No steps selected. Returning to menu.")
            self.pause()
            return
        
        # Get paths from configuration (session-based only)
        config = get_config()
        default_db_path = config.get_database_path()
        default_json_dir = config.get_api_sync_path()
        
        db_path = self.get_user_input("Database file path", default_db_path)
        json_dir = self.get_user_input("JSON files directory", default_json_dir)
        
        print(f"\n🔧 Executing custom workflow...")
        
        # Execute selected steps
        if steps["analysis"]:
            result = self.runner.analyze_json_files(json_dir)
            self.print_result(result, "JSON Analysis")
        
        if steps["recreation"]:
            result = self.runner.recreate_json_tables(db_path)
            self.print_result(result, "Table Recreation")
        
        if steps["population"]:
            result = self.runner.populate_tables(db_path, json_dir)
            self.print_result(result, "Data Population")
        
        if steps["verification"]:
            result = self.runner.verify_tables(db_path)
            self.print_result(result, "Table Verification")
        
        if steps["summary"]:
            result = self.runner.generate_summary_report(db_path)
            self.print_result(result, "Summary Report")
        
        print("\n✅ Custom workflow completed!")
        self.pause()

    def show_configuration(self):
        """Show current configuration"""
        self.clear_screen()
        self.print_header("Current Configuration")
        
        print("\n📋 Default Paths:")
        print(f"   • Database: {self.runner.db_path}")
        print(f"   • JSON Directory: {self.runner.json_dir}")
        
        print(f"\n📁 Path Status:")
        print(f"   • Database exists: {'✅' if self.runner.db_path.exists() else '❌'}")
        print(f"   • JSON directory exists: {'✅' if self.runner.json_dir.exists() else '❌'}")
        
        # Show available JSON files if directory exists
        if self.runner.json_dir.exists():
            json_files = list(self.runner.json_dir.glob("*.json"))
            print(f"\n📄 JSON Files Found: {len(json_files)}")
            for json_file in json_files[:5]:
                print(f"   • {json_file.name}")
            if len(json_files) > 5:
                print(f"   ... and {len(json_files) - 5} more files")
        
        self.pause()


def main():
    """Main entry point for wrapper"""
    try:
        wrapper = JSON2DBSyncWrapper()
        wrapper.show_main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
