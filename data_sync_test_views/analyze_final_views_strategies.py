#!/usr/bin/env python3
"""
FINAL Views Duplicate Handling Strategy Analysis
Identifies which views use different duplicate handling approaches.
Uses the local config.py for easy database access.
"""
import sqlite3
import re
from typing import Dict, List, Tuple, Any
from config import get_database_path


class FinalViewsAnalyzer:
    """Analyzer for FINAL views duplicate handling strategies"""
    
    def __init__(self):
        self.db_path = get_database_path()
        self.final_views = []
        self.strategies = {
            "csv_only": [],
            "left_join_coalesce": [],
            "union_based": [],
            "unknown": []
        }
        
    def connect_database(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_final_views(self) -> List[str]:
        """Get list of all FINAL views"""
        if self.final_views:
            return self.final_views
            
        try:
            conn = self.connect_database()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='view' AND name LIKE 'FINAL_%' 
                ORDER BY name
            """)
            
            self.final_views = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return self.final_views
            
        except Exception as e:
            print(f"❌ Error getting FINAL views: {e}")
            return []
    
    def get_view_sql_definition(self, view_name: str) -> str:
        """Get the SQL definition of a view"""
        try:
            conn = self.connect_database()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='view' AND name = ?
            """, (view_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else ""
            
        except Exception as e:
            print(f"❌ Error getting SQL for {view_name}: {e}")
            return ""
    
    def analyze_duplicate_strategy(self, view_name: str, sql_definition: str) -> Dict[str, Any]:
        """Analyze the duplicate handling strategy for a view"""
        sql_lower = sql_definition.lower()
        
        strategy_info = {
            "view_name": view_name,
            "strategy": "unknown",
            "confidence": "low",
            "evidence": [],
            "potential_issues": [],
            "data_sources": {"csv": False, "json": False}
        }
        
        # Check for data sources
        if "csv_" in sql_lower:
            strategy_info["data_sources"]["csv"] = True
        if "json_" in sql_lower:
            strategy_info["data_sources"]["json"] = True
        
        # Strategy 1: CSV-only (ignores JSON data)
        if strategy_info["data_sources"]["csv"] and not strategy_info["data_sources"]["json"]:
            strategy_info["strategy"] = "csv_only"
            strategy_info["confidence"] = "high"
            strategy_info["evidence"].append("Only references CSV tables")
            strategy_info["potential_issues"].append("Completely ignores JSON data")
        
        # Strategy 2: LEFT JOIN with COALESCE
        elif "left join" in sql_lower and "coalesce" in sql_lower:
            strategy_info["strategy"] = "left_join_coalesce"
            strategy_info["confidence"] = "high"
            strategy_info["evidence"].append("Uses LEFT JOIN with COALESCE")
            
            # Check priority (JSON over CSV or CSV over JSON)
            coalesce_matches = re.findall(r'coalesce\s*\([^)]+\)', sql_lower)
            if coalesce_matches:
                first_coalesce = coalesce_matches[0]
                if "json" in first_coalesce and "csv" in first_coalesce:
                    if first_coalesce.find("json") < first_coalesce.find("csv"):
                        strategy_info["evidence"].append("Prioritizes JSON over CSV")
                    else:
                        strategy_info["evidence"].append("Prioritizes CSV over JSON")
        
        # Strategy 3: UNION-based
        elif "union" in sql_lower:
            strategy_info["strategy"] = "union_based"
            strategy_info["confidence"] = "high"
            strategy_info["evidence"].append("Uses UNION to combine sources")
            
            # Check if it's UNION ALL (potential duplicates) or UNION (deduplicates)
            if "union all" in sql_lower:
                strategy_info["potential_issues"].append("UNION ALL may create duplicates")
            else:
                strategy_info["evidence"].append("UNION automatically deduplicates")
        
        # Check for other patterns
        if "distinct" in sql_lower:
            strategy_info["evidence"].append("Uses DISTINCT for deduplication")
        
        # Check for complex joins
        join_types = ["inner join", "left join", "right join", "full join"]
        join_count = sum(1 for join_type in join_types if join_type in sql_lower)
        if join_count > 1:
            strategy_info["evidence"].append(f"Multiple joins detected ({join_count})")
        
        return strategy_info
    
    def analyze_all_views(self) -> Dict[str, Any]:
        """Analyze duplicate handling strategies for all FINAL views"""
        views = self.get_final_views()
        
        if not views:
            return {"error": "No FINAL views found"}
        
        analysis_results = {
            "total_views": len(views),
            "strategies": {
                "csv_only": [],
                "left_join_coalesce": [],
                "union_based": [],
                "unknown": []
            },
            "view_details": {},
            "summary": {}
        }
        
        print(f"🔍 Analyzing {len(views)} FINAL views for duplicate handling strategies...\n")
        
        for view_name in views:
            print(f"Analyzing: {view_name}")
            
            sql_definition = self.get_view_sql_definition(view_name)
            if not sql_definition:
                print(f"  ❌ Could not get SQL definition")
                continue
            
            strategy_info = self.analyze_duplicate_strategy(view_name, sql_definition)
            strategy = strategy_info["strategy"]
            
            analysis_results["strategies"][strategy].append(view_name)
            analysis_results["view_details"][view_name] = strategy_info
            
            print(f"  📋 Strategy: {strategy.upper()}")
            print(f"  📊 Confidence: {strategy_info['confidence']}")
            if strategy_info["evidence"]:
                print(f"  ✅ Evidence: {', '.join(strategy_info['evidence'])}")
            if strategy_info["potential_issues"]:
                print(f"  ⚠️  Issues: {', '.join(strategy_info['potential_issues'])}")
            print()
        
        # Generate summary
        analysis_results["summary"] = self._generate_strategy_summary(analysis_results)
        
        return analysis_results
    
    def _generate_strategy_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of strategy analysis"""
        total = analysis_results["total_views"]
        strategies = analysis_results["strategies"]
        
        summary = {
            "total_views_analyzed": total,
            "strategy_distribution": {},
            "problematic_views": [],
            "effective_views": [],
            "recommendations": []
        }
        
        # Calculate distribution
        for strategy, views in strategies.items():
            count = len(views)
            percentage = (count / total * 100) if total > 0 else 0
            summary["strategy_distribution"][strategy] = {
                "count": count,
                "percentage": round(percentage, 1),
                "views": views
            }
        
        # Identify problematic views
        problematic = []
        effective = []
        
        for view_name, details in analysis_results["view_details"].items():
            if details["potential_issues"]:
                problematic.append({
                    "view": view_name,
                    "strategy": details["strategy"],
                    "issues": details["potential_issues"]
                })
            elif details["strategy"] == "left_join_coalesce":
                effective.append({
                    "view": view_name,
                    "strategy": details["strategy"],
                    "evidence": details["evidence"]
                })
        
        summary["problematic_views"] = problematic
        summary["effective_views"] = effective
        
        # Generate recommendations
        recommendations = []
        
        if strategies["csv_only"]:
            recommendations.append(
                f"Consider integrating JSON data for {len(strategies['csv_only'])} CSV-only views: "
                f"{', '.join(strategies['csv_only'])}"
            )
        
        if strategies["unknown"]:
            recommendations.append(
                f"Review {len(strategies['unknown'])} views with unknown strategies: "
                f"{', '.join(strategies['unknown'])}"
            )
        
        if strategies["left_join_coalesce"]:
            recommendations.append(
                f"The {len(strategies['left_join_coalesce'])} LEFT JOIN+COALESCE views appear well-designed"
            )
        
        summary["recommendations"] = recommendations
        
        return summary
    
    def print_detailed_report(self, analysis_results: Dict[str, Any]):
        """Print a detailed analysis report"""
        if "error" in analysis_results:
            print(f"❌ {analysis_results['error']}")
            return
        
        summary = analysis_results["summary"]
        
        print("=" * 80)
        print("FINAL VIEWS DUPLICATE HANDLING STRATEGY ANALYSIS")
        print("=" * 80)
        
        print(f"\n📊 OVERVIEW")
        print(f"Total FINAL views analyzed: {summary['total_views_analyzed']}")
        
        print(f"\n📈 STRATEGY DISTRIBUTION")
        for strategy, info in summary["strategy_distribution"].items():
            print(f"  {strategy.upper().replace('_', ' ')}: {info['count']} views ({info['percentage']}%)")
            if info["views"]:
                for view in info["views"]:
                    print(f"    - {view}")
        
        if summary["problematic_views"]:
            print(f"\n⚠️  PROBLEMATIC VIEWS ({len(summary['problematic_views'])})")
            for item in summary["problematic_views"]:
                print(f"  📛 {item['view']} ({item['strategy']})")
                for issue in item["issues"]:
                    print(f"     Issue: {issue}")
        
        if summary["effective_views"]:
            print(f"\n✅ EFFECTIVE VIEWS ({len(summary['effective_views'])})")
            for item in summary["effective_views"]:
                print(f"  ✅ {item['view']} ({item['strategy']})")
                for evidence in item["evidence"]:
                    print(f"     {evidence}")
        
        if summary["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 80)


def main():
    """Main analysis function"""
    analyzer = FinalViewsAnalyzer()
    
    print("=== FINAL Views Duplicate Handling Strategy Analysis ===\n")
    print(f"Database: {analyzer.db_path}\n")
    
    # Run analysis
    results = analyzer.analyze_all_views()
    
    # Print detailed report
    analyzer.print_detailed_report(results)
    
    return results


if __name__ == "__main__":
    main()
