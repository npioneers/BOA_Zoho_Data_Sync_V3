"""
Data Sync Test Views Configuration
Simplified configuration for test scripts in data_sync_test_views workspace.
Points to the correct production database for FINAL views analysis.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional


class TestViewsConfig:
    """Configuration for data sync test views analysis"""
    
    def __init__(self):
        # Define the correct database path relative to this workspace
        # From data_sync_test_views, go up one level and then to data/database/production.db
        self.workspace_dir = Path(__file__).parent
        self.database_path = self.workspace_dir / ".." / "data" / "database" / "production.db"
        
    def get_database_path(self) -> str:
        """Get absolute path to the production database"""
        return str(self.database_path.resolve())
    
    def get_database_dir(self) -> str:
        """Get directory containing the database"""
        return str(self.database_path.parent.resolve())
    
    def validate_database_exists(self) -> bool:
        """Check if the database file exists"""
        return self.database_path.exists()
    
    def get_workspace_dir(self) -> str:
        """Get the test views workspace directory"""
        return str(self.workspace_dir.resolve())
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information for debugging"""
        return {
            "workspace_dir": self.get_workspace_dir(),
            "database_path": self.get_database_path(),
            "database_exists": self.validate_database_exists(),
            "database_size_mb": self._get_database_size_mb() if self.validate_database_exists() else 0
        }
    
    def _get_database_size_mb(self) -> float:
        """Get database file size in MB"""
        try:
            size_bytes = self.database_path.stat().st_size
            return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            return 0.0


# Global config instance for easy access
_test_config = None

def get_test_config() -> TestViewsConfig:
    """Get the test configuration instance"""
    global _test_config
    if _test_config is None:
        _test_config = TestViewsConfig()
    return _test_config

def get_database_path() -> str:
    """Convenient function to get database path directly"""
    return get_test_config().get_database_path()

def validate_setup() -> Dict[str, Any]:
    """Validate the test environment setup"""
    config = get_test_config()
    info = config.get_config_info()
    
    validation = {
        "valid": config.validate_database_exists(),
        "database_path": info["database_path"],
        "database_exists": info["database_exists"],
        "database_size_mb": info["database_size_mb"],
        "workspace_dir": info["workspace_dir"]
    }
    
    if not validation["valid"]:
        validation["error"] = f"Database not found at: {info['database_path']}"
    else:
        validation["message"] = f"Database found ({info['database_size_mb']} MB)"
    
    return validation


if __name__ == "__main__":
    # Test the configuration when run directly
    print("=== Data Sync Test Views Configuration ===")
    
    config = get_test_config()
    validation = validate_setup()
    
    print(f"Workspace Directory: {validation['workspace_dir']}")
    print(f"Database Path: {validation['database_path']}")
    print(f"Database Exists: {validation['database_exists']}")
    
    if validation['valid']:
        print(f"Database Size: {validation['database_size_mb']} MB")
        print("✅ Configuration is valid - ready for test scripts")
    else:
        print(f"❌ {validation['error']}")
        print("Please ensure the database file exists at the specified location")
