#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Display start message
echo -e "${CYAN}Installing argos_node...${NC}"

# Ensure the script is run with sudo
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This script must be run as root.${NC}" 1>&2
    exit 1
fi

# Define source and target directories
SOURCE_DIR="/argos_master"
TARGET_DIR="/home/thales/Argos"

# Check if the target directory exists and create it if not
echo -e "${YELLOW}Checking the existance of the target directory $TARGET_DIR...${NC}"
if [[ ! -d "$TARGET_DIR" ]]; then
    if mkdir -p "$TARGET_DIR"; then
        echo -e "${GREEN}Target directory $TARGET_DIR created successfully.${NC}"
    else
        echo -e "${RED}Failed to create target directory $TARGET_DIR.${NC}" 1>&2
        exit 1
    fi
else
    echo -e "${GREEN}Target directory $TARGET_DIR already exists.${NC}"
fi

# Copy .so files from source to target directory if they are not already there
echo -e "${YELLOW}Checking the existance of the necessary .so files in target directory...${NC}"
for so_file in "$SOURCE_DIR/so"/*.so; do
    if [[ -f "$so_file" ]]; then
        base_name=$(basename "$so_file")
        if [[ ! -f "$TARGET_DIR/$base_name" ]]; then
            echo -e "${YELLOW}Copying $base_name to $TARGET_DIR${NC}"
            if cp "$so_file" "$TARGET_DIR/"; then
                echo -e "${GREEN}Copied $base_name to $TARGET_DIR successfully.${NC}"
            else
                echo -e "${RED}Failed to copy $base_name to $TARGET_DIR.${NC}" 1>&2
            fi
        else
            echo -e "${GREEN}$base_name already exists in $TARGET_DIR. Skipping copy.${NC}"
        fi
    fi
done

# Recreate the virtual environment in the target directory
VENV_DIR="$TARGET_DIR/venv"
if [[ -d "$VENV_DIR" ]]; then
    echo -e "${YELLOW}Removing existing virtual environment at $VENV_DIR${NC}"
    if rm -rf "$VENV_DIR"; then
        echo -e "${GREEN}Removed existing virtual environment at $VENV_DIR successfully.${NC}"
    else
        echo -e "${RED}Failed to remove virtual environment at $VENV_DIR.${NC}" 1>&2
        exit 1
    fi
fi

echo -e "${YELLOW}Creating virtual environment at $VENV_DIR${NC}"
if python3 -m venv "$VENV_DIR"; then
    echo -e "${GREEN}Virtual environment created at $VENV_DIR successfully.${NC}"
else
    echo -e "${RED}Failed to create virtual environment at $VENV_DIR.${NC}" 1>&2
    exit 1
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Gather all .whl files and install them in a single command
WHL_FILES=$(find "$SOURCE_DIR/whl" -name '*.whl' -print | tr '\n' ' ')
if [[ -n "$WHL_FILES" ]]; then
    echo -e "${YELLOW}Installing .whl files into the virtual environment${NC}"
    if pip install $WHL_FILES --no-index --find-links "$SOURCE_DIR/whl"; then
        echo -e "${GREEN}All .whl files installed successfully.${NC}"
    else
        echo -e "${RED}Failed to install .whl files.${NC}" 1>&2
        exit 1
    fi
else
    echo -e "${YELLOW}No .whl files found in $SOURCE_DIR/whl.${NC}"
fi

# Display finish message
echo -e "${CYAN}Installation successfull!${NC}"