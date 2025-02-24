#!/bin/bash

# Check if folder path is provided as argument
if [ $# -eq 0 ]; then
    echo "Error: Please provide the folder path as an argument"
    echo "Usage: ./index_codebase.sh <folder_path>"
    exit 1
fi

# Get the folder path from command line argument
folder_path="$1"

# Check if the folder exists
if [ ! -d "$folder_path" ]; then
    echo "Error: Directory '$folder_path' does not exist"
    exit 1
fi

echo "Processing the directory at $folder_path..."

# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run scripts with the folder_path using python3 instead of python
python3 -m Preprocessing.preprocessing "$folder_path"
python3 -m vector_database.create_tables "$folder_path"

echo "Processing complete."

echo "Please run python app.py <absolute_path_to_folder> to run the server"
