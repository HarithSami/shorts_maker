#!/bin/bash
set -e

SCRIPT_NAME="main.py"
VENV_NAME="venv"

echo "------------------------------------------"
echo "Checking for Python Virtual Environment..."
echo "------------------------------------------"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment '$VENV_NAME'..."
    python3 -m venv "$VENV_NAME" || {
        echo "ERROR: Failed to create virtual environment. Make sure 'python3' is in your PATH."
        exit 1
    }
else
    echo "Virtual environment '$VENV_NAME' already exists."
fi

echo
echo "------------------------------------------"
echo "Activating and installing requirements..."
echo "------------------------------------------"

# Activate the venv
source "$VENV_NAME/bin/activate" || {
    echo "ERROR: Virtual environment activation script not found. Check the venv creation step."
    exit 1
}

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing/Updating dependencies from requirements.txt..."
    pip install -r requirements.txt || {
        echo "ERROR: Failed to install requirements."
        deactivate
        exit 1
    }
else
    echo "WARNING: 'requirements.txt' not found. Skipping dependency installation."
fi

echo
echo "------------------------------------------"
echo "Running the Python script..."
echo "------------------------------------------"

# Run the main Python script
if [ -f "$SCRIPT_NAME" ]; then
    python "$SCRIPT_NAME" || echo "ERROR: The script '$SCRIPT_NAME' encountered an error."
else
    echo "ERROR: The script '$SCRIPT_NAME' was not found in the current directory."
fi

echo
echo "------------------------------------------"
echo "Deactivating Virtual Environment"
echo "------------------------------------------"
deactivate

echo
echo "Process complete."
