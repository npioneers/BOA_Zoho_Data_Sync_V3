"""
Comprehensive Sync Manager and Reporting System

This module provides the highest-level interface for JSON-to-database synchronization
with comprehensive reporting, verification, and monitoring capabilities.

Key Features:
- Complete sync workflow orchestration from JSON to database
- Comprehensive analysis and verification reporting
- JSON vs database comparison with detailed metrics
- Import plan generation and execution tracking
- Multi-format report generation (JSON, CSV, Markdown)
- Success rate monitoring and recommendations
- Production-ready error handling and logging

Architecture:
SyncManager -> Analysis -> Planning -> Import -> Verification -> Reporting -> Summary
"""

import logging
import sqlite3
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from .config import ConfigurationManager
from .enhanced_orchestrator import EnhancedRebuildOrchestrator, SyncSummary
from .enhanced_import_engine import EnhancedImportEngine
from .json_db_mappings import get_all_entities, get_entity_json_mapping

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Result of JSON vs Database comparison"""
    entity_name: str
    json_records: int
    database_records: int
    difference: int
    sync_percentage: float
    status: str
    status_icon: str


@dataclass
class ComprehensiveReport:
    """Comprehensive sync and analysis report"""
    timestamp: str
    session_id: str
    summary_stats: Dict[str, Any]
    entity_comparisons: List[ComparisonResult]
    verification_details: Dict[str, Any]
    recommendations: List[str]
    data_sources: Dict[str, str]
    execution_metrics: Dict[str, Any]


class ComprehensiveSyncManager:
    """
    Comprehensive manager for JSON-to-database synchronization with full reporting
    
    This is the main production interface that coordinates:
    1. Data source analysis and discovery
    2. JSON vs database comparison
    3. Import planning and execution
    4. Comprehensive verification
    5. Multi-format report generation
    6. Success monitoring and recommendations
    """
    
    def __init__(self, config: Optional[ConfigurationManager] = None):
        """Initialize the comprehensive sync manager"""
        self.config = config or ConfigurationManager()
        self.database_path = str(self.config.get('data_sources', 'target_database'))
        
        # Initialize components
        self.orchestrator = EnhancedRebuildOrchestrator(
            database_path=self.database_path,
            config=self.config
        )
        self.import_engine = EnhancedImportEngine(
            database_path=self.database_path,
            config=self.config
        )
        
        # Session tracking
        self.session_id = f"comprehensive_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.reports_dir = Path.cwd() / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"Comprehensive Sync Manager initialized - Session: {self.session_id}")
    
    def execute_comprehensive_sync(self, 
                                 json_directory: str, 
                                 generate_reports: bool = True,
                                 auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Execute the complete comprehensive sync workflow
        
        Args:
            json_directory: Path to directory containing JSON files
            generate_reports: Whether to generate comprehensive reports
            auto_confirm: Whether to auto-confirm import operations
            
        Returns:
            Complete sync results with comprehensive reporting
        """
        logger.info("🚀 Starting Comprehensive JSON-to-Database Sync Workflow")
        logger.info(f"📁 JSON Directory: {json_directory}")
        logger.info(f"🗄️ Database: {self.database_path}")
        logger.info(f"📊 Session ID: {self.session_id}")
        
        workflow_results = {
            'session_id': self.session_id,
            'success': False,
            'analysis': {},
            'comparison': {},
            'import_plan': {},
            'execution': {},
            'verification': {},
            'reports': {},
            'summary': {},
            'recommendations': []
        }
        
        try:
            # Step 1: Comprehensive Data Analysis
            logger.info("📊 Step 1: Performing comprehensive data analysis...")
            analysis_results = self._perform_comprehensive_analysis(json_directory)
            workflow_results['analysis'] = analysis_results
            
            if not analysis_results['success']:
                logger.error("❌ Analysis failed - stopping workflow")
                return workflow_results
            
            # Step 2: JSON vs Database Comparison
            logger.info("🔍 Step 2: Comparing JSON data with database...")
            comparison_results = self._perform_json_db_comparison(analysis_results['loaded_data'])
            workflow_results['comparison'] = comparison_results
            
            # Step 3: Generate Import Plan
            logger.info("📋 Step 3: Generating import plan...")
            import_plan = self._generate_import_plan(analysis_results, comparison_results)
            workflow_results['import_plan'] = import_plan
            
            # Step 4: User Confirmation (if not auto-confirm)
            if not auto_confirm:
                logger.info("⏸️ User confirmation required...")
                confirmed = self._request_user_confirmation(import_plan)
                if not confirmed:
                    logger.info("🚫 Import cancelled by user")
                    workflow_results['user_cancelled'] = True
                    return workflow_results
            
            # Step 5: Execute Import Plan
            logger.info("⚡ Step 5: Executing import plan...")
            execution_results = self._execute_import_plan(import_plan, analysis_results['loaded_data'])
            workflow_results['execution'] = execution_results
            
            # Step 6: Comprehensive Verification
            logger.info("✅ Step 6: Performing comprehensive verification...")
            verification_results = self._perform_comprehensive_verification(analysis_results['loaded_data'])
            workflow_results['verification'] = verification_results
            
            # Step 7: Generate Comprehensive Reports
            if generate_reports:
                logger.info("📄 Step 7: Generating comprehensive reports...")
                reports = self._generate_comprehensive_reports(workflow_results)
                workflow_results['reports'] = reports
            
            # Step 8: Generate Summary and Recommendations
            logger.info("🎯 Step 8: Generating summary and recommendations...")
            summary = self._generate_final_summary(workflow_results)
            workflow_results['summary'] = summary
            
            # Determine overall success
            workflow_results['success'] = (
                execution_results.get('success', False) and
                verification_results.get('overall_success_rate', 0) >= 95.0
            )
            
            if workflow_results['success']:
                logger.info("🎉 Comprehensive sync workflow completed successfully!")
            else:
                logger.warning("⚠️ Sync workflow completed with issues")
            
        except Exception as e:
            logger.error(f"❌ Comprehensive sync workflow failed: {str(e)}")
            workflow_results['error'] = str(e)
            workflow_results['success'] = False
        
        return workflow_results
    
    def _perform_comprehensive_analysis(self, json_directory: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of JSON files"""
        analysis = {
            'success': False,
            'json_directory': json_directory,
            'entities_found': [],
            'total_files': 0,
            'total_records': 0,
            'loaded_data': {},
            'file_details': {},
            'errors': []
        }
        
        try:
            json_path = Path(json_directory)
            if not json_path.exists():
                analysis['errors'].append(f"JSON directory not found: {json_directory}")
                return analysis
            
            # Discover and analyze JSON files
            for entity in get_all_entities():
                entity_files = list(json_path.glob(f"**/{entity.lower()}.json"))
                if entity_files:
                    # Use most recent file
                    latest_file = max(entity_files, key=lambda x: x.stat().st_mtime)
                    
                    # Load and analyze the file
                    file_analysis = self._analyze_json_file(latest_file, entity)
                    if file_analysis['success']:
                        analysis['entities_found'].append(entity)
                        analysis['loaded_data'][entity] = file_analysis['data']
                        analysis['file_details'][entity] = file_analysis['details']
                        analysis['total_files'] += 1
                        analysis['total_records'] += file_analysis['details']['record_count']
                    else:
                        analysis['errors'].extend(file_analysis['errors'])
            
            analysis['success'] = len(analysis['entities_found']) > 0
            
            logger.info(f"📊 Analysis complete: {analysis['total_files']} files, {analysis['total_records']} records")
            
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed: {str(e)}")
            analysis['errors'].append(f"Analysis failed: {str(e)}")
        
        return analysis
    
    def _analyze_json_file(self, file_path: Path, entity_name: str) -> Dict[str, Any]:
        """Analyze a single JSON file"""
        analysis = {
            'success': False,
            'data': [],
            'details': {
                'file_path': str(file_path),
                'file_size_bytes': 0,
                'record_count': 0,
                'sample_fields': [],
                'custom_fields': []
            },
            'errors': []
        }
        
        try:
            # Get file stats
            analysis['details']['file_size_bytes'] = file_path.stat().st_size
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract records based on structure
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and entity_name.lower() in data:
                records = data[entity_name.lower()]
            else:
                records = []
            
            analysis['data'] = records
            analysis['details']['record_count'] = len(records)
            
            # Analyze sample record
            if records:
                sample_record = records[0]
                analysis['details']['sample_fields'] = list(sample_record.keys())
                
                # Detect custom fields
                entity_mapping = get_entity_json_mapping(entity_name)
                if entity_mapping:
                    mapped_fields = set(entity_mapping.keys())
                    actual_fields = set(sample_record.keys())
                    custom_fields = actual_fields - mapped_fields
                    analysis['details']['custom_fields'] = list(custom_fields)
            
            analysis['success'] = True
            logger.info(f"✅ Analyzed {entity_name}: {len(records)} records")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze {file_path}: {str(e)}")
            analysis['errors'].append(f"File analysis failed: {str(e)}")
        
        return analysis
    
    def _perform_json_db_comparison(self, loaded_data: Dict[str, List]) -> Dict[str, Any]:
        """Perform comprehensive JSON vs database comparison"""
        comparison = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'comparisons': [],
            'summary_stats': {},
            'errors': []
        }
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get database table counts
                db_counts = {}
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        db_counts[table] = cursor.fetchone()[0]
                    except Exception as e:
                        logger.warning(f"Failed to count records in {table}: {str(e)}")
                        db_counts[table] = 0
                
                # Create comparisons
                all_entities = set(loaded_data.keys()) | set(db_counts.keys())
                
                for entity in all_entities:
                    entity_key = entity.lower()
                    json_count = len(loaded_data.get(entity, []))
                    db_count = db_counts.get(entity_key, 0)
                    
                    difference = json_count - db_count
                    
                    # Calculate sync percentage
                    if json_count == 0 and db_count == 0:
                        sync_percentage = 100.0
                        status = "NO DATA"
                        status_icon = "❌"
                    elif json_count == 0:
                        sync_percentage = 0.0
                        status = "MISSING JSON"
                        status_icon = "⚠️"
                    elif db_count == 0:
                        sync_percentage = 0.0
                        status = "NEW ENTITY"
                        status_icon = "📥"
                    elif difference == 0:
                        sync_percentage = 100.0
                        status = "SYNCHRONIZED"
                        status_icon = "✅"
                    else:
                        sync_percentage = min(db_count, json_count) / max(db_count, json_count) * 100
                        if difference > 0:
                            status = f"+{difference} NEW"
                            status_icon = "📈"
                        else:
                            status = f"{difference} FEWER"
                            status_icon = "📉"
                    
                    comparison_result = ComparisonResult(
                        entity_name=entity,
                        json_records=json_count,
                        database_records=db_count,
                        difference=difference,
                        sync_percentage=sync_percentage,
                        status=status,
                        status_icon=status_icon
                    )
                    
                    comparison['comparisons'].append(asdict(comparison_result))
                
                # Calculate summary statistics
                comparisons = comparison['comparisons']
                comparison['summary_stats'] = {
                    'total_entities': len(comparisons),
                    'synchronized_entities': len([c for c in comparisons if c['status'] == 'SYNCHRONIZED']),
                    'entities_with_new_data': len([c for c in comparisons if 'NEW' in c['status']]),
                    'missing_json_entities': len([c for c in comparisons if 'MISSING JSON' in c['status']]),
                    'total_json_records': sum(c['json_records'] for c in comparisons),
                    'total_db_records': sum(c['database_records'] for c in comparisons),
                    'overall_sync_rate': sum(c['sync_percentage'] for c in comparisons) / len(comparisons) if comparisons else 0
                }
                
                comparison['success'] = True
                logger.info("✅ JSON vs Database comparison completed")
                
        except Exception as e:
            logger.error(f"❌ Comparison failed: {str(e)}")
            comparison['errors'].append(f"Comparison failed: {str(e)}")
        
        return comparison
    
    def _generate_import_plan(self, analysis_results: Dict, comparison_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive import plan"""
        plan = {
            'timestamp': datetime.now().isoformat(),
            'entities_to_import': [],
            'total_estimated_records': 0,
            'import_strategy': 'enhanced_import',
            'recommendations': []
        }
        
        for entity, data in analysis_results['loaded_data'].items():
            if data:  # Only plan import for entities with data
                entity_plan = {
                    'entity_name': entity,
                    'record_count': len(data),
                    'import_strategy': 'full_replace',  # Default strategy
                    'custom_fields': analysis_results['file_details'][entity].get('custom_fields', []),
                    'priority': 1
                }
                
                plan['entities_to_import'].append(entity_plan)
                plan['total_estimated_records'] += len(data)
        
        # Add recommendations
        if plan['total_estimated_records'] > 10000:
            plan['recommendations'].append("Large dataset detected - consider batch processing")
        
        if any(ep['custom_fields'] for ep in plan['entities_to_import']):
            plan['recommendations'].append("Custom fields detected - enhanced mapping will be applied")
        
        logger.info(f"📋 Import plan generated: {len(plan['entities_to_import'])} entities, {plan['total_estimated_records']} records")
        
        return plan
    
    def _request_user_confirmation(self, import_plan: Dict) -> bool:
        """Request user confirmation for import plan (simplified for production)"""
        logger.info("📋 Import Plan Summary:")
        logger.info(f"   Entities to import: {len(import_plan['entities_to_import'])}")
        logger.info(f"   Total records: {import_plan['total_estimated_records']}")
        
        # In production, this would be a proper user interface
        # For now, auto-confirm if reasonable plan
        return import_plan['total_estimated_records'] < 100000  # Reasonable limit
    
    def _execute_import_plan(self, import_plan: Dict, loaded_data: Dict) -> Dict[str, Any]:
        """Execute the import plan using enhanced import engine"""
        execution = {
            'success': False,
            'entities_processed': 0,
            'entities_successful': 0,
            'entities_failed': 0,
            'total_records_imported': 0,
            'execution_details': {},
            'errors': []
        }
        
        try:
            for entity_plan in import_plan['entities_to_import']:
                entity_name = entity_plan['entity_name']
                entity_data = loaded_data.get(entity_name, [])
                
                if not entity_data:
                    continue
                
                logger.info(f"⚡ Importing {entity_name}: {len(entity_data)} records")
                
                # Create temporary JSON file for import engine
                temp_file = Path(f"temp_{entity_name}.json")
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(entity_data, f)
                    
                    # Execute import using enhanced import engine
                    import_result = self.import_engine.import_entity_data(
                        entity_name=entity_name,
                        source_file=temp_file,
                        import_strategy=entity_plan['import_strategy'],
                        custom_fields=entity_plan['custom_fields']
                    )
                    
                    execution['execution_details'][entity_name] = asdict(import_result)
                    execution['entities_processed'] += 1
                    
                    if import_result.success:
                        execution['entities_successful'] += 1
                        execution['total_records_imported'] += import_result.records_imported
                        logger.info(f"✅ {entity_name} imported successfully: {import_result.records_imported} records")
                    else:
                        execution['entities_failed'] += 1
                        execution['errors'].extend(import_result.errors)
                        logger.error(f"❌ {entity_name} import failed: {import_result.errors}")
                
                finally:
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()
            
            execution['success'] = execution['entities_failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ Import execution failed: {str(e)}")
            execution['errors'].append(f"Import execution failed: {str(e)}")
        
        return execution
    
    def _perform_comprehensive_verification(self, loaded_data: Dict) -> Dict[str, Any]:
        """Perform comprehensive verification after import"""
        verification = {
            'success': True,
            'entities_verified': 0,
            'entities_passed': 0,
            'entities_failed': 0,
            'overall_success_rate': 0.0,
            'verification_details': {},
            'errors': []
        }
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for entity_name, json_data in loaded_data.items():
                    expected_count = len(json_data)
                    
                    try:
                        # Get actual database count
                        table_name = entity_name.lower()
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        actual_count = cursor.fetchone()[0]
                        
                        # Calculate match percentage
                        if expected_count == 0 and actual_count == 0:
                            match_percentage = 100.0
                        elif expected_count == 0 or actual_count == 0:
                            match_percentage = 0.0
                        else:
                            match_percentage = (min(expected_count, actual_count) / max(expected_count, actual_count)) * 100
                        
                        passed = match_percentage >= 95.0
                        
                        verification['verification_details'][entity_name] = {
                            'expected_records': expected_count,
                            'actual_records': actual_count,
                            'match_percentage': match_percentage,
                            'passed': passed
                        }
                        
                        verification['entities_verified'] += 1
                        if passed:
                            verification['entities_passed'] += 1
                        else:
                            verification['entities_failed'] += 1
                        
                        logger.info(f"✅ {entity_name} verification: {match_percentage:.1f}% match")
                        
                    except Exception as e:
                        logger.error(f"❌ Verification failed for {entity_name}: {str(e)}")
                        verification['errors'].append(f"Verification failed for {entity_name}: {str(e)}")
                        verification['entities_failed'] += 1
                
                # Calculate overall success rate
                if verification['entities_verified'] > 0:
                    verification['overall_success_rate'] = (verification['entities_passed'] / verification['entities_verified']) * 100
                
                verification['success'] = verification['entities_failed'] == 0
                
        except Exception as e:
            logger.error(f"❌ Comprehensive verification failed: {str(e)}")
            verification['errors'].append(f"Verification failed: {str(e)}")
            verification['success'] = False
        
        return verification
    
    def _generate_comprehensive_reports(self, workflow_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive reports in multiple formats"""
        reports = {
            'json_report_path': None,
            'csv_report_path': None,
            'markdown_report_path': None,
            'generation_success': False
        }
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create comprehensive report data
            report_data = ComprehensiveReport(
                timestamp=datetime.now().isoformat(),
                session_id=self.session_id,
                summary_stats=workflow_results.get('comparison', {}).get('summary_stats', {}),
                entity_comparisons=workflow_results.get('comparison', {}).get('comparisons', []),
                verification_details=workflow_results.get('verification', {}).get('verification_details', {}),
                recommendations=workflow_results.get('recommendations', []),
                data_sources={},  # Could be populated from analysis
                execution_metrics=workflow_results.get('execution', {})
            )
            
            # Generate JSON report
            json_report_path = self.reports_dir / f'comprehensive_sync_report_{timestamp}.json'
            with open(json_report_path, 'w') as f:
                json.dump(asdict(report_data), f, indent=2)
            reports['json_report_path'] = str(json_report_path)
            
            # Generate CSV report (entity comparisons)
            if report_data.entity_comparisons:
                df = pd.DataFrame(report_data.entity_comparisons)
                csv_report_path = self.reports_dir / f'entity_comparison_report_{timestamp}.csv'
                df.to_csv(csv_report_path, index=False)
                reports['csv_report_path'] = str(csv_report_path)
            
            # Generate Markdown summary
            markdown_report_path = self.reports_dir / f'sync_summary_report_{timestamp}.md'
            with open(markdown_report_path, 'w') as f:
                f.write(self._generate_markdown_summary(report_data))
            reports['markdown_report_path'] = str(markdown_report_path)
            
            reports['generation_success'] = True
            logger.info(f"📄 Reports generated in: {self.reports_dir}")
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {str(e)}")
            reports['error'] = str(e)
        
        return reports
    
    def _generate_markdown_summary(self, report_data: ComprehensiveReport) -> str:
        """Generate Markdown summary report"""
        md = f"""# Comprehensive Sync Report

**Session ID:** {report_data.session_id}  
**Generated:** {report_data.timestamp}

## Summary Statistics

- **Total Entities:** {report_data.summary_stats.get('total_entities', 0)}
- **Synchronized Entities:** {report_data.summary_stats.get('synchronized_entities', 0)}
- **Entities with New Data:** {report_data.summary_stats.get('entities_with_new_data', 0)}
- **Overall Sync Rate:** {report_data.summary_stats.get('overall_sync_rate', 0):.1f}%

## Entity Comparison

| Entity | JSON Records | DB Records | Status |
|--------|-------------|------------|--------|
"""
        
        for comparison in report_data.entity_comparisons:
            md += f"| {comparison['entity_name']} | {comparison['json_records']:,} | {comparison['database_records']:,} | {comparison['status_icon']} {comparison['status']} |\n"
        
        if report_data.recommendations:
            md += "\n## Recommendations\n\n"
            for rec in report_data.recommendations:
                md += f"- {rec}\n"
        
        return md
    
    def _generate_final_summary(self, workflow_results: Dict) -> Dict[str, Any]:
        """Generate final workflow summary"""
        summary = {
            'session_id': self.session_id,
            'overall_success': workflow_results.get('success', False),
            'entities_analyzed': len(workflow_results.get('analysis', {}).get('entities_found', [])),
            'entities_imported': workflow_results.get('execution', {}).get('entities_successful', 0),
            'total_records_imported': workflow_results.get('execution', {}).get('total_records_imported', 0),
            'verification_success_rate': workflow_results.get('verification', {}).get('overall_success_rate', 0),
            'reports_generated': workflow_results.get('reports', {}).get('generation_success', False),
            'recommendations': []
        }
        
        # Generate recommendations
        if summary['verification_success_rate'] < 95:
            summary['recommendations'].append("Verification success rate below 95% - review import logs")
        
        if summary['entities_imported'] < summary['entities_analyzed']:
            summary['recommendations'].append("Some entities failed to import - check error logs")
        
        if summary['overall_success']:
            summary['recommendations'].append("Sync completed successfully - ready for production use")
        
        return summary


def generate_comparison_report(database_path: str, json_directory: str) -> pd.DataFrame:
    """
    Standalone function to generate JSON vs Database comparison report
    
    Args:
        database_path: Path to SQLite database
        json_directory: Path to JSON files directory
        
    Returns:
        DataFrame with comparison results
    """
    manager = ComprehensiveSyncManager()
    manager.database_path = database_path
    
    # Perform analysis and comparison
    analysis = manager._perform_comprehensive_analysis(json_directory)
    comparison = manager._perform_json_db_comparison(analysis['loaded_data'])
    
    # Convert to DataFrame
    if comparison['success'] and comparison['comparisons']:
        df = pd.DataFrame(comparison['comparisons'])
        return df
    else:
        return pd.DataFrame()  # Empty DataFrame if no results
