"""
CSV Database Rebuild Main Wrapper
User interface wrapper that provides menu-driven functionality
Calls the runner for actual business logic execution
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from runner_csv_db_rebuild import CSVDatabaseRebuildRunner


class CSVDatabaseRebuildMain:
    """
    Main wrapper class providing user interface for CSV database rebuild operations.
    Provides menu-driven interaction and calls runner for business logic.
    """
    
    def __init__(self):
        """Initialize the main wrapper"""
        self.runner = None
        # Paths relative to project root (one level up from csv_db_rebuild)
        self.current_config = {
            "db_path": "../data/database/production.db",
            "csv_dir": "../data/csv/Nangsel Pioneers_Latest",
            "log_dir": "../logs",
            "enable_logging": True
        }
    
    def display_banner(self) -> None:
        """Display application banner"""
        print("=" * 80)
        print("CSV DATABASE REBUILD SYSTEM")
        print("=" * 80)
        print("Rebuild SQLite database from Zoho CSV exports")
        print(f"Current Config: DB={self.current_config['db_path']}, CSV={self.current_config['csv_dir']}")
        print("System will auto-initialize on startup")
        print("=" * 80)
        print()
    
    def display_main_menu(self) -> None:
        """Display the main menu options"""
        print("MAIN MENU:")
        print("1. Clear and Populate All Tables")
        print("2. Populate All Tables (No Clear)")
        print("3. Populate Single Table")
        print("4. Clear All Tables")
        print("5. Clear Single Table")
        print("6. Verify Table Population")
        print("7. Show System Status")
        print("8. Configuration Settings")
        print("9. Show Available Tables")
        print("0. Exit")
        print()
    
    def get_user_input(self, prompt: str, valid_options: Optional[List[str]] = None) -> str:
        """Get validated user input"""
        while True:
            try:
                user_input = input(prompt).strip()
                if valid_options and user_input not in valid_options:
                    print(f"Invalid option. Please choose from: {', '.join(valid_options)}")
                    continue
                return user_input
            except KeyboardInterrupt:
                print("\\nOperation cancelled by user.")
                return "0"
            except EOFError:
                print("\\nInput stream ended.")
                return "0"
    
    def initialize_runner(self) -> bool:
        """Initialize the runner with current configuration"""
        try:
            print("Initializing CSV Database Rebuild System...")
            self.runner = CSVDatabaseRebuildRunner(
                db_path=self.current_config["db_path"],
                csv_dir=self.current_config["csv_dir"],
                enable_logging=self.current_config["enable_logging"],
                log_dir=self.current_config["log_dir"]
            )
            print("System initialized successfully!")
            print(f"Database: {self.current_config['db_path']}")
            print(f"CSV Directory: {self.current_config['csv_dir']}")
            print(f"Logging: {'Enabled' if self.current_config['enable_logging'] else 'Disabled'}")
            return True
        except Exception as e:
            print(f"Failed to initialize system: {str(e)}")
            return False
    
    def clear_and_populate_all_tables_menu(self) -> None:
        """Menu for clearing and populating all tables"""
        print("\\nClear and Populate All Tables")
        print("This will:")
        print("1. Clear all existing data from csv_* tables only")
        print("2. Repopulate all tables from CSV files")
        print("\\nSAFETY: Only tables with 'csv_' prefix will be cleared - other database tables are protected.")
        print("WARNING: This will permanently delete all existing data from csv_* tables!")
        confirm = self.get_user_input("Continue? (yes/no): ")
        
        if confirm.lower() != "yes":
            print("Operation cancelled.")
            return
        
        try:
            print("\\nStarting clear and populate process...")
            result = self.runner.clear_and_populate_all_tables()
            
            print("\\nCLEAR AND POPULATE COMPLETE!")
            print(f"Tables Cleared: {result['tables_cleared']}/{result['tables_attempted']}")
            print(f"Rows Cleared: {result['total_rows_cleared']:,}")
            print(f"Tables Populated: {result['tables_populated']}/{result['tables_attempted']}")
            print(f"Overall Success Rate: {result['overall_success_rate']:.1f}%")
            print(f"Total Records Inserted: {result['total_records_inserted']:,}")
            print(f"Total Processing Time: {result['total_processing_time_seconds']:.1f} seconds")
            
            if result['failed_tables']:
                print(f"Failed Tables: {', '.join(result['failed_tables'])}")
            else:
                print("All tables cleared and populated successfully!")
            
        except Exception as e:
            print(f"Clear and populate operation failed: {str(e)}")

    def populate_all_tables_menu(self) -> None:
        """Menu for populating all tables (without clearing first)"""
        print("\\nPopulating All Tables...")
        print("This will populate all tables from CSV files.")
        print("Note: Use option 1 if you want to clear tables first.")
        confirm = self.get_user_input("Continue? (y/n): ", ["y", "n", "Y", "N"])
        
        if confirm.lower() != "y":
            print("Operation cancelled.")
            return
            return
        
        try:
            print("\\nStarting population process...")
            result = self.runner.populate_all_tables()
            
            print("\\nPOPULATION COMPLETE!")
            print(f"Tables Successful: {result['tables_successful']}/{result['tables_attempted']}")
            print(f"Overall Success Rate: {result['overall_success_rate']:.1f}%")
            print(f"Total Records: {result['total_records_inserted']:,}")
            print(f"Processing Time: {result['processing_time_seconds']:.1f} seconds")
            
            if result['failed_tables']:
                print(f"Failed Tables: {', '.join(result['failed_tables'])}")
            
        except Exception as e:
            print(f"Population failed: {str(e)}")
    
    def populate_single_table_menu(self) -> None:
        """Menu for populating a single table"""
        # Show available tables
        available_tables = list(self.runner.table_mappings.keys())
        print("\\nAvailable Tables:")
        for i, table in enumerate(available_tables, 1):
            print(f"{i}. {table}")
        
        table_choice = self.get_user_input("\\nEnter table number or name: ")
        
        # Handle numeric input
        if table_choice.isdigit():
            table_index = int(table_choice) - 1
            if 0 <= table_index < len(available_tables):
                table_name = available_tables[table_index]
            else:
                print("Invalid table number.")
                return
        else:
            # Handle direct table name input
            if table_choice in available_tables:
                table_name = table_choice
            else:
                print(f"Table '{table_choice}' not found.")
                return
        
        print(f"\\nPopulating table: {table_name}")
        confirm = self.get_user_input("Continue? (y/n): ", ["y", "n", "Y", "N"])
        
        if confirm.lower() != "y":
            print("Operation cancelled.")
            return
        
        try:
            result = self.runner.populate_single_table(table_name)
            
            if result['success']:
                success_rate = (result['records'] / result['csv_records'] * 100) if result['csv_records'] > 0 else 0
                print(f"\\nSUCCESS: {table_name}")
                print(f"Records Inserted: {result['records']}/{result['csv_records']} ({success_rate:.1f}%)")
            else:
                print(f"\\nFAILED: {table_name}")
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"Population failed: {str(e)}")
    
    def clear_all_tables_menu(self) -> None:
        """Menu for clearing all tables"""
        print("\\nClear All Tables")
        print("WARNING: This will permanently delete all data from csv_* tables only!")
        print("SAFETY: Only tables with 'csv_' prefix will be affected - other database tables are protected.")
        confirm = self.get_user_input("Are you sure? (yes/no): ")
        
        if confirm.lower() != "yes":
            print("Operation cancelled.")
            return
        
        try:
            tables_cleared = 0
            total_tables = len(self.runner.table_mappings)
            
            print("\\nClearing tables...")
            for table_name in self.runner.table_mappings.keys():
                result = self.runner.clear_table(table_name)
                if result['success']:
                    print(f"Cleared {table_name}: {result['rows_deleted']} rows deleted")
                    tables_cleared += 1
                else:
                    print(f"Failed to clear {table_name}: {result['error']}")
            
            print(f"\\nClearing complete: {tables_cleared}/{total_tables} tables cleared successfully")
            
        except Exception as e:
            print(f"Clear operation failed: {str(e)}")
    
    def clear_single_table_menu(self) -> None:
        """Menu for clearing a single table"""
        # Show available tables
        available_tables = list(self.runner.table_mappings.keys())
        print("\\nAvailable Tables:")
        for i, table in enumerate(available_tables, 1):
            print(f"{i}. {table}")
        
        table_choice = self.get_user_input("\\nEnter table number or name: ")
        
        # Handle numeric input
        if table_choice.isdigit():
            table_index = int(table_choice) - 1
            if 0 <= table_index < len(available_tables):
                table_name = available_tables[table_index]
            else:
                print("Invalid table number.")
                return
        else:
            # Handle direct table name input
            if table_choice in available_tables:
                table_name = table_choice
            else:
                print(f"Table '{table_choice}' not found.")
                return
        
        print(f"\\nClear table: {table_name}")
        print("WARNING: This will permanently delete all data from this table!")
        confirm = self.get_user_input("Continue? (y/n): ", ["y", "n", "Y", "N"])
        
        if confirm.lower() != "y":
            print("Operation cancelled.")
            return
        
        try:
            result = self.runner.clear_table(table_name)
            
            if result['success']:
                print(f"\\nSUCCESS: Cleared {table_name}")
                print(f"Rows deleted: {result['rows_deleted']}")
            else:
                print(f"\\nFAILED: {result['error']}")
                
        except Exception as e:
            print(f"Clear operation failed: {str(e)}")
    
    def verify_table_population_menu(self) -> None:
        """Menu for verifying table population"""
        print("\\nTable Population Verification")
        print("1. Verify All Tables")
        print("2. Verify Single Table")
        
        choice = self.get_user_input("Enter choice (1-2): ", ["1", "2"])
        
        if choice == "1":
            self._verify_all_tables()
        elif choice == "2":
            self._verify_single_table()
    
    def _verify_all_tables(self) -> None:
        """Verify all tables"""
        try:
            summary = self.runner.get_table_status_summary()
            
            print("\\nTABLE VERIFICATION REPORT")
            print("=" * 60)
            print(f"Total Tables: {summary['total_tables']}")
            print(f"Populated Tables: {summary['populated_tables']}")
            print(f"Population Rate: {summary['population_rate']:.1f}%")
            print(f"Total Records: {summary['total_records']:,}")
            print()
            
            print(f"{'Table Name':<25} | {'Status':<10} | {'Records':<10}")
            print("-" * 50)
            
            for table_name, status in summary['table_status'].items():
                if status['success']:
                    status_text = "OK" if status['record_count'] > 0 else "EMPTY"
                    print(f"{table_name:<25} | {status_text:<10} | {status['record_count']:<10,}")
                else:
                    print(f"{table_name:<25} | {'ERROR':<10} | {'N/A':<10}")
            
        except Exception as e:
            print(f"Verification failed: {str(e)}")
    
    def _verify_single_table(self) -> None:
        """Verify a single table"""
        available_tables = list(self.runner.table_mappings.keys())
        print("\\nAvailable Tables:")
        for i, table in enumerate(available_tables, 1):
            print(f"{i}. {table}")
        
        table_choice = self.get_user_input("\\nEnter table number or name: ")
        
        # Handle numeric input
        if table_choice.isdigit():
            table_index = int(table_choice) - 1
            if 0 <= table_index < len(available_tables):
                table_name = available_tables[table_index]
            else:
                print("Invalid table number.")
                return
        else:
            # Handle direct table name input
            if table_choice in available_tables:
                table_name = table_choice
            else:
                print(f"Table '{table_choice}' not found.")
                return
        
        try:
            result = self.runner.verify_table_population(table_name)
            
            print(f"\\nVerification Results for {table_name}:")
            if result['success']:
                print(f"Status: OK")
                print(f"Record Count: {result['record_count']:,}")
                print(f"Column Count: {result['column_count']}")
            else:
                print(f"Status: ERROR")
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"Verification failed: {str(e)}")
    
    def show_system_status(self) -> None:
        """Show current system status"""
        print("\\nSYSTEM STATUS")
        print("=" * 50)
        print(f"Initialized: {'Yes' if self.runner else 'No'}")
        print(f"Database Path: {self.current_config['db_path']}")
        print(f"CSV Directory: {self.current_config['csv_dir']}")
        print(f"Log Directory: {self.current_config['log_dir']}")
        print(f"Logging Enabled: {self.current_config['enable_logging']}")
        
        # Check if paths exist
        db_path = Path(self.current_config['db_path'])
        csv_path = Path(self.current_config['csv_dir'])
        
        print(f"Database Exists: {'Yes' if db_path.exists() else 'No'}")
        print(f"CSV Directory Exists: {'Yes' if csv_path.exists() else 'No'}")
        
        if csv_path.exists():
            csv_files = list(csv_path.glob("*.csv"))
            print(f"CSV Files Found: {len(csv_files)}")
        
        if self.runner:
            print(f"Mapped Tables: {len(self.runner.table_mappings)}")
    
    def configuration_menu(self) -> None:
        """Configuration settings menu"""
        print("\\nCONFIGURATION SETTINGS")
        print("1. Change Database Path")
        print("2. Change CSV Directory")
        print("3. Change Log Directory")
        print("4. Toggle Logging")
        print("5. Show Current Configuration")
        print("6. Reset to Defaults")
        print("0. Back to Main Menu")
        
        choice = self.get_user_input("Enter choice (0-6): ", ["0", "1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            new_path = input("Enter new database path: ").strip()
            if new_path:
                self.current_config['db_path'] = new_path
                print(f"Database path updated to: {new_path}")
                print("Re-initializing system with new configuration...")
                self.initialize_runner()
        
        elif choice == "2":
            new_path = input("Enter new CSV directory: ").strip()
            if new_path:
                self.current_config['csv_dir'] = new_path
                print(f"CSV directory updated to: {new_path}")
                print("Re-initializing system with new configuration...")
                self.initialize_runner()
        
        elif choice == "3":
            new_path = input("Enter new log directory: ").strip()
            if new_path:
                self.current_config['log_dir'] = new_path
                print(f"Log directory updated to: {new_path}")
                print("Re-initializing system with new configuration...")
                self.initialize_runner()
        
        elif choice == "4":
            self.current_config['enable_logging'] = not self.current_config['enable_logging']
            status = "enabled" if self.current_config['enable_logging'] else "disabled"
            print(f"Logging {status}")
            print("Re-initializing system with new configuration...")
            self.initialize_runner()
        
        elif choice == "5":
            print("\\nCurrent Configuration:")
            for key, value in self.current_config.items():
                print(f"  {key}: {value}")
        
        elif choice == "6":
            self.current_config = {
                "db_path": "data/database/production.db",
                "csv_dir": "data/csv/Nangsel Pioneers_Latest",
                "log_dir": "logs",
                "enable_logging": True
            }
            print("Configuration reset to defaults")
            print("Re-initializing system with default configuration...")
            self.initialize_runner()
    
    def show_available_tables(self) -> None:
        """Show available tables and their mappings"""
        print("\\nAVAILABLE TABLES AND MAPPINGS")
        print("=" * 60)
        print(f"{'Table Name':<25} | {'CSV File':<30}")
        print("-" * 60)
        
        for table_name, mapping in self.runner.table_mappings.items():
            csv_file = mapping.get('csv_file', 'N/A')
            print(f"{table_name:<25} | {csv_file:<30}")
        
        print(f"\\nTotal Tables: {len(self.runner.table_mappings)}")
    
    def run(self) -> None:
        """Main application loop"""
        try:
            self.display_banner()
            
            # Automatically initialize the system
            print("Initializing system...")
            if not self.initialize_runner():
                print("Failed to initialize system. Exiting.")
                return
            print()
            
            while True:
                self.display_main_menu()
                choice = self.get_user_input("Enter your choice (0-9): ", 
                                           ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
                
                print()  # Add spacing
                
                if choice == "0":
                    print("Exiting CSV Database Rebuild System. Goodbye!")
                    break
                
                elif choice == "1":
                    self.clear_and_populate_all_tables_menu()
                
                elif choice == "2":
                    self.populate_all_tables_menu()
                
                elif choice == "3":
                    self.populate_single_table_menu()
                
                elif choice == "4":
                    self.clear_all_tables_menu()
                
                elif choice == "5":
                    self.clear_single_table_menu()
                
                elif choice == "6":
                    self.verify_table_population_menu()
                
                elif choice == "7":
                    self.show_system_status()
                
                elif choice == "8":
                    self.configuration_menu()
                
                elif choice == "9":
                    self.show_available_tables()
                
                print("\\nPress Enter to continue...")
                input()
                
        except KeyboardInterrupt:
            print("\\n\\nApplication interrupted by user. Exiting...")
        except Exception as e:
            print(f"\\nUnexpected error: {str(e)}")
            print("Application will exit.")


def main():
    """Entry point for the CSV Database Rebuild System"""
    app = CSVDatabaseRebuildMain()
    app.run()


if __name__ == "__main__":
    main()
