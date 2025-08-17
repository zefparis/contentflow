@echo off
echo Testing Python execution...

python -c "print('Hello from Python!')"

echo.
echo Python version:
python --version

echo.
echo Python path:
where python

echo.
echo Environment variables:
echo DATABASE_URL=...%DATABASE_URL:~-20% 2>nul
echo PYTHONPATH=%PYTHONPATH%

echo.
pause
