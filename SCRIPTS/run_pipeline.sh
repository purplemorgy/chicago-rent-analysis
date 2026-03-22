#!/bin/bash

# ============================================================
# Chicago Rent Analysis
#
# This script:
#   1. sets up a virtual environment
#   2. installs required packages
#   3. pulls Git LFS files if available
#   4. runs data cleaning
#   5. runs EDA plots
#   6. runs panel regressions
#
# Run using: bash run_pipeline.sh
# ============================================================

set -e

REPO_ROOT="$(pwd)"

# If script is launched from inside SCRIPTS, move up one level
if [ "$(basename "$REPO_ROOT")" = "SCRIPTS" ]; then
    REPO_ROOT="$(dirname "$REPO_ROOT")"
fi

echo "=========================================="
echo "Chicago Rent Analysis Reproduction Script"
echo "Repo root: $REPO_ROOT"
echo "=========================================="

cd "$REPO_ROOT"

echo ""
echo "[1/6] Checking for Git LFS..."
if command -v git-lfs >/dev/null 2>&1; then
    git lfs install
    git lfs pull
    echo "Git LFS files pulled successfully."
else
    echo "Git LFS is not installed."
fi

echo ""
echo "[2/6] Creating virtual environment..."
python3 -m venv venv

echo ""
echo "[3/6] Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment activation script not found."
    exit 1
fi
echo ""
echo "[4/6] Installing required packages..."
pip install --upgrade pip
pip install pandas matplotlib numpy statsmodels

echo ""
echo "[5/6] Running data cleaning..."
python "$REPO_ROOT/SCRIPTS/data_cleaning.py"

echo ""
echo "[6/6] Running exploratory data analysis..."
python "$REPO_ROOT/SCRIPTS/eda.py" --coverage --rent-growth-dist --business-dist --scatter

echo ""
echo "[7/7] Running panel regression models..."
python "$REPO_ROOT/SCRIPTS/panel_regression.py" --all --interpret

echo ""
echo "=========================================="
echo "Pipeline succesfully completed."
echo "=========================================="
