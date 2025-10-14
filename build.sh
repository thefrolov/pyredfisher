#!/bin/bash
# Build script for creating PyPI distribution packages

set -e

echo "=== Building rackfish distribution packages ==="

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info rackfish.egg-info

# Build wheel and source distribution
echo "Building packages..."
python -m build

echo ""
echo "=== Build complete! ==="
echo ""
echo "Distribution packages created in dist/:"
ls -lh dist/
echo ""
echo "To upload to PyPI Test:"
echo "  python -m twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI:"
echo "  python -m twine upload dist/*"
