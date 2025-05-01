#!/bin/bash
# Script to build and publish the package to PyPI

set -e  # Exit on error

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "Building package..."
python -m pip install --upgrade build
python -m build

# Check the package
echo "Checking package with twine..."
python -m pip install --upgrade twine
python -m twine check dist/*

# Upload to PyPI (uncomment when ready)
echo "Ready to upload to PyPI"
echo "Run the following command when you're ready:"
echo "python -m twine upload dist/*"
# python -m twine upload dist/*