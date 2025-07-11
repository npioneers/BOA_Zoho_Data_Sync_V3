"""
JSON2DB Sync Main Wrapper
User-friendly interface with menus for JSON to Database synchronization.
Provides interactive menus and calls runner functions.
"""
import os
import sys
from pathlib import Path
from typing import Optional

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
            print("   2. Recreate JSON Tables (Recommended)")
            print("   3. Populate Tables with Data")
            print("   4. Verify Tables")
            print("   5. Generate Summary Report")
            print("   6. Full Sync Workflow")
            print("   7. Advanced Options")
            print("   0. Exit")
            
            choice = input("\nSelect an option (0-7): ").strip()
            
            if choice == '1':
                self.handle_json_analysis()
            elif choice == '2':
                self.handle_table_recreation()
            elif choice == '3':
                self.handle_data_population()
            elif choice == '4':
                self.handle_table_verification()
            elif choice == '5':
                self.handle_summary_report()
            elif choice == '6':
                self.handle_full_workflow()
            elif choice == '7':
                self.show_advanced_menu()
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 0-7.")
                self.pause()

    def show_advanced_menu(self):
        """Display advanced options menu"""
        while True:
            self.clear_screen()
            self.print_header("JSON2DB Sync - Advanced Options")
            
            print("\n⚙️ Advanced Operations:")
            print("   1. Create All Tables (Full Creation)")
            print("   2. Generate Table Schemas Only")
            print("   3. Custom Workflow Configuration")
            print("   4. Check Current Configuration")
            print("   0. Back to Main Menu")
            
            choice = input("\nSelect an option (0-4): ").strip()
            
            if choice == '1':
                self.handle_full_table_creation()
            elif choice == '2':
                self.handle_schema_generation()
            elif choice == '3':
                self.handle_custom_workflow()
            elif choice == '4':
                self.show_configuration()
            elif choice == '0':
                break
            else:
                print("\n❌ Invalid choice. Please select 0-4.")
                self.pause()

    def handle_json_analysis(self):
        """Handle JSON file analysis"""
        self.clear_screen()
        self.print_header("JSON File Analysis")
        
        print("\n📁 This will analyze JSON files to understand their structure.")
        
        # Get JSON directory from configuration
        config = get_config()
        default_json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                           else config.get_consolidated_path())
        json_dir = self.get_user_input("JSON files directory", default_json_dir)
        
        if not Path(json_dir).exists():
            print(f"\n❌ Directory not found: {json_dir}")
            self.pause()
            return
        
        print(f"\n🔍 Analyzing JSON files in: {json_dir}")
        result = self.runner.analyze_json_files(json_dir)
        
        self.print_result(result, "JSON Analysis")
        
        if result.get("success"):
            schema_analysis = result.get("schema_analysis", {})
            if schema_analysis:
                print(f"\n📋 Found {len(schema_analysis)} JSON file types")
                for file_type, analysis in list(schema_analysis.items())[:5]:
                    print(f"   • {file_type}: {analysis.get('total_records', 0)} records")
                if len(schema_analysis) > 5:
                    print(f"   ... and {len(schema_analysis) - 5} more types")
        
        self.pause()

    def handle_table_recreation(self):
        """Handle JSON table recreation"""
        self.clear_screen()
        self.print_header("Recreate JSON Tables")
        
        print("\n🔄 This will recreate JSON tables in the existing database.")
        print("   • Preserves database file and other tables")
        print("   • Recommended for regular operations")
        
        # Get database path
        default_db_path = "data/database/production.db"
        db_path = self.get_user_input("Database file path", default_db_path)
        
        if not self.confirm_action("\nProceed with table recreation?"):
            return
        
        print(f"\n🔄 Recreating JSON tables in: {db_path}")
        result = self.runner.recreate_json_tables(db_path)
        
        self.print_result(result, "Table Recreation")
        self.pause()

    def handle_data_population(self):
        """Handle data population"""
        self.clear_screen()
        self.print_header("Populate Tables with Data")
        
        print("\n📊 This will populate JSON tables with data from JSON files.")
        
        # Get paths from configuration
        config = get_config()
        default_db_path = config.get_database_path()
        default_json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                           else config.get_consolidated_path())
        
        db_path = self.get_user_input("Database file path", default_db_path)
        json_dir = self.get_user_input("JSON files directory", default_json_dir)
        
        # Check if paths exist
        if not Path(db_path).exists():
            print(f"\n❌ Database file not found: {db_path}")
            self.pause()
            return
        
        if not Path(json_dir).exists():
            print(f"\n❌ JSON directory not found: {json_dir}")
            self.pause()
            return
        
        # Ask about cutoff filtering
        use_cutoff = self.confirm_action("\nUse date cutoff filtering (recommended)?")
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
        
        if not self.confirm_action(f"\nProceed with data population?" + 
                                 (f" (filtering last {cutoff_days} days)" if cutoff_days else "")):
            return
        
        print(f"\n📊 Populating tables...")
        result = self.runner.populate_tables(db_path, json_dir, cutoff_days)
        
        self.print_result(result, "Data Population")
        self.pause()

    def handle_table_verification(self):
        """Handle table verification"""
        self.clear_screen()
        self.print_header("Verify Tables")
        
        print("\n✅ This will verify the structure and data of JSON tables.")
        
        default_db_path = "data/database/production.db"
        db_path = self.get_user_input("Database file path", default_db_path)
        
        if not Path(db_path).exists():
            print(f"\n❌ Database file not found: {db_path}")
            self.pause()
            return
        
        print(f"\n✅ Verifying tables in: {db_path}")
        result = self.runner.verify_tables(db_path)
        
        self.print_result(result, "Table Verification")
        self.pause()

    def handle_summary_report(self):
        """Handle summary report generation"""
        self.clear_screen()
        self.print_header("Generate Summary Report")
        
        print("\n📋 This will generate a comprehensive summary report.")
        
        default_db_path = "data/database/production.db"
        db_path = self.get_user_input("Database file path", default_db_path)
        
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
                print(f"   • Total tables: {report.get('total_tables', 'N/A')}")
                print(f"   • Total records: {report.get('total_records', 'N/A')}")
        
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
        
        # Get configuration from config system
        config = get_config()
        default_db_path = config.get_database_path()
        default_json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                           else config.get_consolidated_path())
        
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
        
        default_db_path = "data/database/production.db"
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
        default_json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                           else config.get_consolidated_path())
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
        
        # Get paths from configuration
        config = get_config()
        default_db_path = config.get_database_path()
        default_json_dir = (config.get_api_sync_path() if config.is_api_sync_mode() 
                           else config.get_consolidated_path())
        
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
