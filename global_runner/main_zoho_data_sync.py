"""
Global Zoho Data Sync Wrapper
User interface wrapper with menu system for orchestrating api_sync, json2db_sync, and csv_db_rebuild packages.
Provides interactive menu for users to manage the complete sync pipeline.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from global_runner.runner_zoho_data_sync import GlobalSyncRunner
from global_runner.config import GlobalSyncConfig


class GlobalSyncWrapper:
    """
    User interface wrapper for global Zoho data sync operations.
    Provides interactive menu system and user-friendly operations.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the global sync wrapper.
        
        Args:
            config_file: Path to configuration file
        """
        self.config = GlobalSyncConfig(config_file)
        self.runner = GlobalSyncRunner(config_file, enable_logging=True)
        
        # Display configuration
        self.use_colors = self.config.get('ui.use_colors', True)
        self.show_details = self.config.get('ui.show_detailed_output', True)
        self.auto_freshness_check = self.config.get('ui.auto_freshness_check_on_startup', True)
    
    def _print_header(self, title: str) -> None:
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def _print_subheader(self, title: str) -> None:
        """Print formatted subheader"""
        print(f"\n--- {title} ---")
    
    def _print_status(self, message: str, status: str = "info") -> None:
        """Print status message with optional color coding"""
        if self.use_colors:
            colors = {
                "success": "\033[92m✓\033[0m",  # Green
                "warning": "\033[93m⚠\033[0m",  # Yellow
                "error": "\033[91m✗\033[0m",    # Red
                "info": "\033[94mℹ\033[0m"     # Blue
            }
            prefix = colors.get(status, "")
        else:
            prefix = {"success": "✓", "warning": "⚠", "error": "✗", "info": "ℹ"}.get(status, "")
        
        print(f"{prefix} {message}")
    
    def _print_table(self, headers: list, rows: list, title: str = None) -> None:
        """Print formatted table"""
        if title:
            self._print_subheader(title)
        
        if not rows:
            print("No data to display")
            return
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(header_row)
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row[:len(col_widths)]))
            print(row_str)
    
    def _get_user_input(self, prompt: str, valid_options: list = None) -> str:
        """Get user input with validation"""
        while True:
            try:
                user_input = input(f"\n{prompt}: ").strip()
                
                if valid_options and user_input not in valid_options:
                    print(f"Invalid option. Please choose from: {', '.join(valid_options)}")
                    continue
                
                return user_input
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                return "4"  # Exit option
            except EOFError:
                print("\nEnd of input reached.")
                return "4"  # Exit option
    
    def display_freshness_status(self, freshness_result: Dict[str, Any]) -> None:
        """Display database freshness status in a user-friendly format"""
        self._print_subheader("Database Freshness Status")
        
        if not freshness_result.get("success", False):
            self._print_status(f"Freshness check failed: {freshness_result.get('error', 'Unknown error')}", "error")
            return
        
        # Overall status
        overall_status = freshness_result.get("overall_status", "unknown")
        status_messages = {
            "fresh": ("All data is up to date", "success"),
            "stale": ("Some data is outdated", "warning"),
            "empty": ("Database appears to be empty", "warning"),
            "unknown": ("Status unknown", "info")
        }
        
        message, status_type = status_messages.get(overall_status, ("Unknown status", "info"))
        self._print_status(message, status_type)
        
        # Summary stats
        print(f"\nSummary:")
        print(f"  Tables checked: {freshness_result.get('tables_checked', 0)}")
        print(f"  Fresh tables: {freshness_result.get('fresh_tables', 0)}")
        print(f"  Stale tables: {freshness_result.get('stale_tables', 0)}")
        print(f"  Threshold: {freshness_result.get('threshold_days', 1)} days")
        
        # Detailed table status
        if self.show_details and freshness_result.get("table_details"):
            table_data = []
            for table_name, details in freshness_result["table_details"].items():
                status = details.get("status", "unknown")
                record_count = details.get("record_count", 0)
                days_old = details.get("days_old")
                
                if days_old is not None:
                    age_str = f"{days_old} days"
                else:
                    age_str = "N/A"
                
                # Status indicators
                status_indicators = {
                    "fresh": "✓ Fresh",
                    "stale": "⚠ Stale", 
                    "empty": "⚠ Empty",
                    "missing": "✗ Missing",
                    "no_dates": "? No dates",
                    "no_date_column": "? No date col",
                    "date_error": "✗ Date error",
                    "error": "✗ Error"
                }
                
                status_display = status_indicators.get(status, status)
                table_data.append([table_name, status_display, f"{record_count:,}", age_str])
            
            if table_data:
                self._print_table(
                    ["Table", "Status", "Records", "Age"],
                    table_data,
                    "Table Details"
                )
    
    def display_sync_results(self, sync_result: Dict[str, Any]) -> None:
        """Display sync pipeline results in a user-friendly format"""
        self._print_subheader("Sync Pipeline Results")
        
        if not sync_result.get("success", False):
            self._print_status("Sync pipeline failed", "error")
            if "error" in sync_result:
                print(f"Error: {sync_result['error']}")
        else:
            self._print_status("Sync pipeline completed successfully", "success")
        
        # Pipeline stages
        completed_stages = sync_result.get("stages_completed", [])
        failed_stages = sync_result.get("stages_failed", [])
        
        print(f"\nPipeline Summary:")
        print(f"  Completed stages: {len(completed_stages)}")
        print(f"  Failed stages: {len(failed_stages)}")
        
        if sync_result.get("total_processing_time"):
            print(f"  Total time: {sync_result['total_processing_time']:.1f} seconds")
        
        # Stage details
        if self.show_details:
            stage_data = []
            all_stages = ["api_sync", "json2db_sync", "freshness_check"]
            
            for stage in all_stages:
                if stage in completed_stages:
                    status = "✓ Completed"
                elif stage in failed_stages:
                    status = "✗ Failed"
                else:
                    status = "- Skipped"
                
                stage_data.append([stage.replace("_", " ").title(), status])
            
            self._print_table(
                ["Stage", "Status"],
                stage_data,
                "Stage Details"
            )
        
        # Show freshness results if available
        if sync_result.get("freshness_check_result"):
            print()  # Add spacing
            self.display_freshness_status(sync_result["freshness_check_result"])
    
    def display_system_status(self, status_result: Dict[str, Any]) -> None:
        """Display system status in a user-friendly format"""
        self._print_subheader("System Status")
        
        # Database status
        db_status = status_result.get("database_status", {})
        if db_status.get("exists", False):
            if db_status.get("accessible", False):
                self._print_status(f"Database: Connected ({db_status.get('table_count', 0)} tables, {db_status.get('size_mb', 0):.1f} MB)", "success")
            else:
                self._print_status(f"Database: Connection failed - {db_status.get('error', 'Unknown error')}", "error")
        else:
            self._print_status("Database: Not found", "warning")
        
        # Package status
        package_status = status_result.get("package_status", {})
        package_data = []
        
        for package_name, details in package_status.items():
            enabled = details.get("enabled", False)
            path_exists = details.get("path_exists", False)
            runner_available = details.get("runner_available", False)
            
            if enabled and path_exists and runner_available:
                status = "✓ Ready"
            elif enabled and path_exists:
                status = "⚠ No runner"
            elif enabled:
                status = "✗ Path missing"
            else:
                status = "- Disabled"
            
            package_data.append([package_name.replace("_", " ").title(), status])
        
        if package_data:
            self._print_table(
                ["Package", "Status"],
                package_data,
                "Package Availability"
            )
        
        # Configuration
        config_info = status_result.get("configuration", {})
        print(f"\nConfiguration:")
        print(f"  API Sync: Uses intelligent timestamp detection")
        print(f"  Freshness threshold: {config_info.get('freshness_threshold', 'N/A')} days")
        print(f"  Logging: {'Enabled' if config_info.get('logging_enabled', False) else 'Disabled'}")
    
    def show_help(self) -> None:
        """Display help information"""
        self._print_header("Global Zoho Data Sync - Help")
        
        print("This tool orchestrates the complete Zoho data synchronization pipeline.")
        print("The pipeline consists of three main stages:")
        print()
        print("1. API Sync (api_sync package)")
        print("   - Fetches latest data from Zoho APIs")
        print("   - Stores raw JSON data for processing")
        print()
        print("2. JSON2DB Sync (json2db_sync package)")
        print("   - Processes JSON data into structured database tables")
        print("   - Handles data transformation and normalization")
        print()
        print("3. Freshness Check")
        print("   - Analyzes data currency and completeness")
        print("   - Provides recommendations for sync frequency")
        print()
        print("Menu Options:")
        print("1. Run Full Sync - Execute complete pipeline (API → JSON2DB → Check)")
        print("2. Check Freshness - Analyze current data freshness only") 
        print("3. System Status - Display package and database status")
        print("4. Help - Show this help information")
        print("5. Exit - Close the application")
        print()
        print("Configuration:")
        print(f"Database: {self.config.get_database_path()}")
        print(f"API Sync: Uses intelligent timestamp detection")
        print(f"Freshness threshold: {self.config.get('sync_pipeline.freshness_threshold_days', 1)} days")
        
        # Package paths
        print("\nPackage Locations:")
        for package_name in ['api_sync', 'json2db_sync', 'csv_db_rebuild']:
            package_config = self.config.get_package_config(package_name)
            if package_config:
                print(f"{package_name}: {package_config['path']}")
    
    def run_startup_checks(self) -> None:
        """Run startup checks and display initial status"""
        self._print_header("Global Zoho Data Sync - Startup")
        
        # Show system status
        system_status = self.runner.get_system_status()
        self.display_system_status(system_status)
        
        # Auto freshness check if enabled
        if self.auto_freshness_check:
            print()  # Add spacing
            freshness_result = self.runner.check_database_freshness()
            self.display_freshness_status(freshness_result)
            
            # Provide sync recommendation
            overall_status = freshness_result.get("overall_status", "unknown")
            if overall_status == "stale":
                print()
                self._print_status("Recommendation: Run full sync to update stale data", "info")
            elif overall_status == "empty":
                print()
                self._print_status("Recommendation: Run full sync to populate database", "info")
    
    def run_interactive_menu(self) -> None:
        """Run the main interactive menu loop"""
        try:
            self.run_startup_checks()
            
            while True:
                self._print_header("Global Zoho Data Sync - Main Menu")
                
                print("Choose an option:")
                print("1. Run Full Sync Pipeline")
                print("2. Check Database Freshness")
                print("3. View System Status")
                print("4. Help")
                print("5. Exit")
                
                choice = self._get_user_input("Enter your choice (1-5)", ["1", "2", "3", "4", "5"])
                
                if choice == "1":
                    self._handle_full_sync()
                elif choice == "2":
                    self._handle_freshness_check()
                elif choice == "3":
                    self._handle_system_status()
                elif choice == "4":
                    self.show_help()
                elif choice == "5":
                    self._print_status("Thank you for using Global Zoho Data Sync!", "info")
                    break
                else:
                    self._print_status("Invalid choice. Please try again.", "warning")
                
                if choice != "5":
                    input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user. Goodbye!")
        except Exception as e:
            self._print_status(f"Unexpected error: {str(e)}", "error")
            print("Please check the logs for more details.")
    
    def _handle_full_sync(self) -> None:
        """Handle full sync pipeline execution"""
        self._print_header("Run Full Sync Pipeline")
        
        # Confirm before starting
        print(f"\nThis will run the complete sync pipeline using intelligent timestamp detection.")
        print("Stages: API Sync → JSON2DB Sync → Freshness Check")
        
        confirm = self._get_user_input("Continue? (y/n)", ["y", "n", "Y", "N"])
        if confirm.lower() != "y":
            self._print_status("Full sync cancelled", "info")
            return
        
        # Run sync (no cutoff_days parameter needed - using intelligent detection)
        self._print_status("Starting full sync pipeline...", "info")
        sync_result = self.runner.run_full_sync()
        
        # Display results
        print()  # Add spacing
        self.display_sync_results(sync_result)
    
    def _handle_freshness_check(self) -> None:
        """Handle freshness check execution"""
        self._print_header("Check Database Freshness")
        
        self._print_status("Running freshness analysis...", "info")
        freshness_result = self.runner.check_database_freshness()
        
        print()  # Add spacing
        self.display_freshness_status(freshness_result)
    
    def _handle_system_status(self) -> None:
        """Handle system status display"""
        self._print_header("System Status")
        
        self._print_status("Checking system status...", "info")
        status_result = self.runner.get_system_status()
        
        print()  # Add spacing
        self.display_system_status(status_result)


def main():
    """Main entry point for the global sync wrapper"""
    try:
        # Initialize wrapper with optional config file
        config_file = None
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        
        wrapper = GlobalSyncWrapper(config_file)
        wrapper.run_interactive_menu()
        
    except Exception as e:
        print(f"Error initializing Global Zoho Data Sync: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
