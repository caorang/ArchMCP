#!/bin/bash
# Run comprehensive test suite

cd "$(dirname "$0")/.."

echo "🧪 Starting Comprehensive Test Suite"
echo "======================================"
echo ""
echo "This will run 30 tests:"
echo "  - 15 keyword mode tests"
echo "  - 15 description mode tests"
echo ""
echo "Results will be saved to: outputs/comprehensive_test_results.docx"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Run tests
python tests/comprehensive_test.py

echo ""
echo "✅ Done! Open outputs/comprehensive_test_results.docx to review results"
