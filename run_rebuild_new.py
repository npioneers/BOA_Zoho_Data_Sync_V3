#!/usr/bin/env python3
"""
Project Bedrock V3 - Complete Database Rebuild Entry Point

This script provides a simplified entry point for the complete database rebuild
process using the RebuildOrchestrator. The orchestrator manages all aspects
of the ETL pipeline including safety protocols, schema creation, data transformation,
and validation.

Usage:
    python run_rebuild.py                    # Clean rebuild (default)
    python run_rebuild.py --append          # Append to existing data
    python run_rebuild.py --database custom.db  # Use custom database

Features:
- Clean and simple orchestration through RebuildOrchestrator
- Comprehensive error handling and logging
- Real-time progress tracking
- Complete processing statistics
- Production-ready data pipeline execution
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_pipeline.orchestrator import RebuildOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rebuild_process.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the database rebuild process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Execute complete database rebuild using RebuildOrchestrator'
    )
    parser.add_argument(
        '--append', 
        action='store_true', 
        help='Append to existing data instead of clean rebuild'
    )
    parser.add_argument(
        '--database', 
        type=str, 
        help='Path to database file (optional)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine rebuild mode
    clean_rebuild = not args.append
    
    logger.info("🚀 Project Bedrock V3 - Database Rebuild Process")
    logger.info("=" * 60)
    logger.info(f"📋 Configuration:")
    logger.info(f"   🔄 Mode: {'Clean Rebuild' if clean_rebuild else 'Append Mode'}")
    if args.database:
        logger.info(f"   🗄️ Database: {args.database}")
    logger.info(f"   📝 Log Level: {'DEBUG' if args.verbose else 'INFO'}")
    logger.info("")
    
    try:
        # Create and execute orchestrator
        orchestrator = RebuildOrchestrator(database_path=args.database)
        
        # Execute the complete rebuild process
        processing_stats = orchestrator.run_full_rebuild(clean_rebuild=clean_rebuild)
        
        # Display final summary
        summary = orchestrator.get_processing_summary()
        
        logger.info("📊 FINAL PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🎯 Success: {'✅ YES' if summary['success'] else '❌ NO'}")
        logger.info(f"📈 Entities Processed: {summary['entities_processed']}/{summary['entities_in_manifest']}")
        logger.info(f"📥 Total Input Records: {summary['total_input_records']:,}")
        logger.info(f"📤 Total Output Records: {summary['total_output_records']:,}")
        logger.info(f"⏱️ Processing Duration: {summary['duration_seconds']:.2f} seconds")
        logger.info(f"🚀 Processing Rate: {summary['records_per_second']:.0f} records/second")
        
        if summary['processing_errors']:
            logger.warning(f"⚠️ Processing Errors ({len(summary['processing_errors'])}):")
            for error in summary['processing_errors']:
                logger.warning(f"   💥 {error}")
        
        # Display validation results
        if summary['validation_results']:
            logger.info(f"\n🔍 Database Validation Results:")
            for entity, results in summary['validation_results'].items():
                header_count = results['header_records']
                line_items_count = results.get('line_items_records', 0)
                if line_items_count > 0:
                    logger.info(f"   ✅ {entity}: {header_count:,} headers, {line_items_count:,} line items")
                else:
                    logger.info(f"   ✅ {entity}: {header_count:,} records")
        
        # Final result
        if summary['success']:
            logger.info("\n🎉 DATABASE REBUILD COMPLETED SUCCESSFULLY! 🎉")
            return 0
        else:
            logger.error("\n❌ DATABASE REBUILD COMPLETED WITH ERRORS")
            return 1
            
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: Database rebuild failed")
        logger.error(f"💥 Error Details: {str(e)}")
        
        # Log full traceback for debugging
        import traceback
        logger.debug("Full traceback:")
        logger.debug(traceback.format_exc())
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
