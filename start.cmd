@echo off

:: Activate Python virtual environment (if applicable)
:: call venv\Scripts\activate

:: Run the Python script
python sim-checker.py

:: Keep the window open after execution
echo.
echo Press any key to exit...
pause > nul