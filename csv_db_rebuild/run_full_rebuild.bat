@echo off
echo ========================================
echo CSV to Database Rebuild Process V2.0
echo ========================================
echo.

echo Step 1: Running CSV Database Rebuild...
python -c "from csv_db_rebuild.runner_csv_db_rebuild import CSVDatabaseRebuildRunner; runner = CSVDatabaseRebuildRunner(); result = runner.populate_all_tables(); print(f'Success Rate: {result[\"overall_success_rate\"]:.1f}%')"
if %errorlevel% neq 0 (
    echo ERROR: Population failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Verifying database integrity...
python verify_schema.py
if %errorlevel% neq 0 (
    echo WARNING: Schema verification issues detected
)

echo.
echo ========================================
echo Rebuild Process Complete!
echo ========================================
echo Check logs/ folder for detailed reports
echo.
echo Alternative: Run 'python main_csv_db_rebuild.py' for interactive mode
echo.
pause
