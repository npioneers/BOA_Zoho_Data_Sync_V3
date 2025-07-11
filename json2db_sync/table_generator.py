"""
Table Generator
Generates database table creation SQL based on JSON analysis results.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Handle imports for both standalone and module usage
try:
    from .json_analyzer import JSONAnalyzer
except ImportError:
    from json_analyzer import JSONAnalyzer


class TableGenerator:
    """Generates database table creation SQL from JSON analysis"""
    
    def __init__(self, json_analyzer: Optional[JSONAnalyzer] = None):
        self.analyzer = json_analyzer or JSONAnalyzer()
        self.setup_logging()
        
        # SQL templates and configurations
        self.sql_templates = {
            'create_table': "CREATE TABLE IF NOT EXISTS {table_name} (\n{columns}\n);",
            'column': "    {name} {type}{nullable}{primary_key}",
            'index': "CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table}({column});",
            'primary_key_constraint': "    PRIMARY KEY ({columns})"
        }
        
        # Data type mappings for optimization
        self.optimized_types = {
            'id_fields': 'INTEGER PRIMARY KEY',
            'small_text': 'VARCHAR(255)',
            'medium_text': 'VARCHAR(1000)', 
            'large_text': 'TEXT',
            'boolean': 'INTEGER',  # SQLite uses 0/1 for boolean
            'decimal': 'DECIMAL(15,2)',  # For monetary values
            'date': 'DATE',
            'datetime': 'DATETIME',
            'timestamp': 'TIMESTAMP'
        }
        
    def setup_logging(self):
        """Setup logging for table generation"""
        self.logger = logging.getLogger(__name__)

    def analyze_and_generate(self) -> Dict[str, Any]:
        """Analyze JSON files and generate table creation SQL"""
        self.logger.info("Starting table generation process...")
        
        # Run analysis if not already done
        if not self.analyzer.analysis_results:
            self.analyzer.analyze_all_json_files()
        
        # Generate SQL for each table
        table_sql = {}
        
        for table_name, table_info in self.analyzer.analysis_results.items():
            self.logger.info(f"Generating SQL for table: {table_name}")
            sql = self.generate_table_sql(table_name, table_info['analysis'])
            table_sql[table_name] = sql
        
        return table_sql

    def generate_table_sql(self, table_name: str, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate SQL statements for a single table"""
        columns = analysis.get('columns', {})
        
        if not columns:
            self.logger.warning(f"No columns found for table {table_name}")
            return {}
        
        # Generate column definitions
        column_defs = []
        primary_keys = []
        indexes = []
        
        # Check if we have a single INTEGER primary key candidate
        single_int_pk = None
        for col_name, col_info in columns.items():
            if (col_info.get('is_primary_key', False) and 
                col_info.get('data_type') == 'INTEGER' and 
                col_name.lower().endswith('_id')):
                single_int_pk = col_name
                break
        
        for col_name, col_info in columns.items():
            # Track primary keys
            if col_info.get('is_primary_key', False):
                primary_keys.append(col_name)
            
            # Generate column definition - pass info about single PK strategy
            col_def = self.generate_column_definition(
                col_name, col_info, 
                is_single_pk=(col_name == single_int_pk)
            )
            column_defs.append(col_def)
            
            # Generate indexes for foreign keys and frequently used fields
            if (col_info.get('is_foreign_key', False) or 
                col_name.lower() in ['email', 'phone', 'name', 'status', 'date']):
                index_sql = self.sql_templates['index'].format(
                    table=table_name,
                    column=col_name
                )
                indexes.append(index_sql)
        
        # Add composite primary key constraint only if no single INTEGER primary key was used
        if primary_keys and not single_int_pk:
            pk_constraint = self.sql_templates['primary_key_constraint'].format(
                columns=', '.join(primary_keys)
            )
            column_defs.append(pk_constraint)
        
        # Generate CREATE TABLE statement
        create_table_sql = self.sql_templates['create_table'].format(
            table_name=table_name,
            columns=',\n'.join(column_defs)
        )
        
        return {
            'create_table': create_table_sql,
            'indexes': indexes,
            'column_count': len(columns),
            'primary_keys': primary_keys
        }

    def generate_column_definition(self, col_name: str, col_info: Dict[str, Any], is_single_pk: bool = False) -> str:
        """Generate SQL column definition"""
        # Determine optimized data type
        data_type = self.optimize_data_type(col_name, col_info)
        
        # Handle nullable constraint - make all columns nullable except primary keys
        nullable = ""
        if col_info.get('is_primary_key', False) and is_single_pk:
            nullable = " NOT NULL"  # Primary keys should not be null
        # All other columns are nullable by default (no constraint needed)
        
        # Handle primary key - only add column-level PRIMARY KEY if this is the single PK
        primary_key = ""
        if col_info.get('is_primary_key', False) and is_single_pk:
            if data_type.startswith('INTEGER'):
                primary_key = " PRIMARY KEY AUTOINCREMENT"
            else:
                primary_key = " PRIMARY KEY"
        
        return self.sql_templates['column'].format(
            name=col_name,
            type=data_type,
            nullable=nullable,
            primary_key=primary_key
        )

    def optimize_data_type(self, col_name: str, col_info: Dict[str, Any]) -> str:
        """Optimize data type based on column name and characteristics"""
        original_type = col_info.get('data_type', 'TEXT')
        max_length = col_info.get('max_length')
        col_name_lower = col_name.lower()
        
        # Handle ID fields
        if col_info.get('is_primary_key', False) and 'id' in col_name_lower:
            return 'INTEGER'
        
        # Handle specific field types by name
        if any(keyword in col_name_lower for keyword in ['email', 'phone', 'url', 'website']):
            return 'VARCHAR(255)'
        
        if any(keyword in col_name_lower for keyword in ['name', 'title', 'description']):
            if max_length and max_length <= 255:
                return 'VARCHAR(255)'
            elif max_length and max_length <= 1000:
                return 'VARCHAR(1000)'
            else:
                return 'TEXT'
        
        if any(keyword in col_name_lower for keyword in ['amount', 'price', 'cost', 'total', 'balance']):
            return 'DECIMAL(15,2)'
        
        if any(keyword in col_name_lower for keyword in ['date', 'time', 'created', 'updated', 'modified']):
            return 'DATETIME'
        
        if any(keyword in col_name_lower for keyword in ['status', 'state', 'type', 'category']):
            return 'VARCHAR(100)'
        
        if any(keyword in col_name_lower for keyword in ['is_', 'has_', 'can_', 'enabled', 'active']):
            return 'INTEGER'  # Boolean fields
        
        # Handle based on original data type and length
        if original_type == 'INTEGER':
            return 'INTEGER'
        elif original_type == 'REAL':
            return 'REAL'
        elif original_type == 'TEXT':
            if max_length:
                if max_length <= 50:
                    return 'VARCHAR(50)'
                elif max_length <= 255:
                    return 'VARCHAR(255)'
                elif max_length <= 1000:
                    return 'VARCHAR(1000)'
            return 'TEXT'
        
        return 'TEXT'  # Default fallback

    def generate_complete_sql_script(self, output_file: Optional[str] = None) -> str:
        """Generate complete SQL script for all tables"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"json2db_sync/sql_schema_{timestamp}.sql"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        # Generate SQL for all tables
        table_sql = self.analyze_and_generate()
        
        # Build complete script
        sql_script = []
        sql_script.append("-- JSON to Database Sync - Generated Schema")
        sql_script.append(f"-- Generated: {datetime.now().isoformat()}")
        sql_script.append(f"-- Source: {self.analyzer.json_dir}")
        sql_script.append("")
        sql_script.append("-- Enable foreign key constraints")
        sql_script.append("PRAGMA foreign_keys = ON;")
        sql_script.append("")
        
        # Main entity tables first
        main_tables = [name for name in table_sql.keys() if '_line_items' not in name]
        line_item_tables = [name for name in table_sql.keys() if '_line_items' in name]
        
        # Create main tables
        sql_script.append("-- Main Entity Tables")
        sql_script.append("-" * 50)
        for table_name in sorted(main_tables):
            sql_info = table_sql[table_name]
            sql_script.append(f"-- Table: {table_name}")
            sql_script.append(sql_info['create_table'])
            sql_script.append("")
        
        # Create line item tables
        if line_item_tables:
            sql_script.append("-- Line Item Tables")
            sql_script.append("-" * 50)
            for table_name in sorted(line_item_tables):
                sql_info = table_sql[table_name]
                sql_script.append(f"-- Table: {table_name}")
                sql_script.append(sql_info['create_table'])
                sql_script.append("")
        
        # Create indexes
        sql_script.append("-- Indexes")
        sql_script.append("-" * 50)
        for table_name, sql_info in table_sql.items():
            for index_sql in sql_info.get('indexes', []):
                sql_script.append(index_sql)
        
        sql_script.append("")
        sql_script.append("-- Schema generation complete")
        
        # Write to file
        complete_sql = '\n'.join(sql_script)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(complete_sql)
            
            self.logger.info(f"Complete SQL schema saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error saving SQL schema: {str(e)}")
            return ""

    def print_table_generation_summary(self):
        """Print summary of table generation"""
        if not self.analyzer.analysis_results:
            self.analyzer.analyze_all_json_files()
        
        table_sql = self.analyze_and_generate()
        
        print("\n" + "="*80)
        print("DATABASE TABLE GENERATION SUMMARY")
        print("="*80)
        
        print(f"Tables to Create: {len(table_sql)}")
        
        total_columns = sum(info.get('column_count', 0) for info in table_sql.values())
        total_indexes = sum(len(info.get('indexes', [])) for info in table_sql.values())
        
        print(f"Total Columns: {total_columns}")
        print(f"Total Indexes: {total_indexes}")
        
        print(f"\nTABLE DETAILS:")
        print("-" * 60)
        print(f"{'Table Name':<25} {'Columns':<10} {'Indexes':<10} {'Primary Key'}")
        print("-" * 60)
        
        for table_name, sql_info in sorted(table_sql.items()):
            pk_info = ', '.join(sql_info.get('primary_keys', ['AUTO']))
            print(f"{table_name:<25} {sql_info.get('column_count', 0):<10} "
                  f"{len(sql_info.get('indexes', [])):<10} {pk_info}")
        
        print("="*80)


def main():
    """Main function to run table generation"""
    # Create analyzer and generator
    analyzer = JSONAnalyzer()
    generator = TableGenerator(analyzer)
    
    try:
        # Print analysis summary first
        analyzer.print_analysis_summary()
        
        # Generate table creation summary
        generator.print_table_generation_summary()
        
        # Generate complete SQL script
        sql_file = generator.generate_complete_sql_script()
        
        print(f"\nComplete SQL schema generated: {sql_file}")
        
    except Exception as e:
        logging.error(f"Table generation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
