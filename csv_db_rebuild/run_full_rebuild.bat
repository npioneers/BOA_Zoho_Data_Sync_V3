@echo off
echo ========================================
echo CSV to Database Rebuild Process
echo ========================================
echo.

echo Step 1: Creating fresh database...
python create_database.py
if %errorlevel% neq 0 (
    echo ERROR: Database creation failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Populating database from CSV files...
python enhanced_population.py
if %errorlevel% neq 0 (
    echo ERROR: Population failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying database integrity...
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
pause
