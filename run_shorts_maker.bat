@echo off
SET SCRIPT_NAME=main.py
SET VENV_NAME=venv

echo ------------------------------------------
echo Checking for Python Virtual Environment...
echo ------------------------------------------

:: Check if the virtual environment directory exists
if not exist "%VENV_NAME%\" (
    echo Creating virtual environment '%VENV_NAME%'...
    python -m venv %VENV_NAME%
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Make sure 'python' is in your PATH.
        goto :eof
    )
) else (
    echo Virtual environment '%VENV_NAME%' already exists.
)

echo.
echo ------------------------------------------
echo Activating and installing requirements...
echo ------------------------------------------

:: Check if the virtual environment activation script exists
if exist "%VENV_NAME%\Scripts\activate.bat" (
    :: Activate the venv
    call "%VENV_NAME%\Scripts\activate.bat"

    :: Check if requirements.txt exists and install dependencies
    if exist "requirements.txt" (
        echo Installing/Updating dependencies from requirements.txt...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ERROR: Failed to install requirements.
            deactivate
            goto :eof
        )
    ) else (
        echo WARNING: 'requirements.txt' not found. Skipping dependency installation.
    )

    echo.
    echo ------------------------------------------
    echo Running the Python script...
    echo ------------------------------------------

    :: Run the main Python script
    if exist "%SCRIPT_NAME%" (
        python "%SCRIPT_NAME%"
        if errorlevel 1 (
            echo ERROR: The script '%SCRIPT_NAME%' encountered an error.
        )
    ) else (
        echo ERROR: The script '%SCRIPT_NAME%' was not found in the current directory.
    )

    echo.
    echo ------------------------------------------
    echo Deactivating Virtual Environment
    echo ------------------------------------------
    deactivate

) else (
    echo ERROR: Virtual environment activation script not found. Check the venv creation step.
)

echo.
echo Process complete.
pause