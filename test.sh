#!/bin/bash
# Quick test script for Ingress to Gateway API Migrator

set -e

echo "🧪 Testing Ingress to Gateway API Migrator"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION installed"
else
    echo -e "${RED}✗${NC} Python 3 is not installed"
    exit 1
fi

# Test 2: Check dependencies
echo ""
echo "2️⃣  Checking dependencies..."
if python3 -c "import yaml" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PyYAML installed"
else
    echo -e "${RED}✗${NC} PyYAML is not installed"
    echo "   Install with: pip install -r requirements.txt"
    exit 1
fi

# Test 3: Test with simple example
echo ""
echo "3️⃣  Testing migration with simple example..."
python3 migrate.py -i examples/sample-ingresses.yaml -g test-gateway \
    -o test-http.yaml -t test-tls.yaml -f test-failed.yaml > /dev/null 2>&1

if [ -f "test-http.yaml" ]; then
    echo -e "${GREEN}✓${NC} HTTPRoutes generated"
else
    echo -e "${RED}✗${NC} Failed to generate HTTPRoutes"
    exit 1
fi

if [ -f "test-tls.yaml" ]; then
    echo -e "${GREEN}✓${NC} TLSRoutes generated"
else
    echo -e "${YELLOW}⚠${NC} No TLSRoutes generated (may be normal)"
fi

# Test 4: YAML validation
echo ""
echo "4️⃣  Validating generated YAML files..."
if python3 -c "import yaml; yaml.safe_load_all(open('test-http.yaml'))" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} HTTPRoutes YAML is valid"
else
    echo -e "${RED}✗${NC} HTTPRoutes YAML is invalid"
    exit 1
fi

# Test 5: Test with advanced example
echo ""
echo "5️⃣  Testing with advanced examples..."
python3 migrate.py -i examples/advanced-ingresses.yaml -g test-gateway \
    -o test-http-adv.yaml -t test-tls-adv.yaml -f test-failed-adv.yaml > /dev/null 2>&1

FAILED_COUNT=$(grep -c "^# Reason:" test-failed-adv.yaml || true)
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} $FAILED_COUNT Ingress not migrated (expected for advanced example)"
else
    echo -e "${GREEN}✓${NC} All advanced Ingresses migrated"
fi

# Test 6: Unit tests (if pytest available)
echo ""
echo "6️⃣  Unit tests..."
if command -v pytest &> /dev/null; then
    if pytest tests/test_migration.py -v --tb=short > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Unit tests passed"
    else
        echo -e "${RED}✗${NC} Unit tests failed"
        echo "   Run: pytest tests/test_migration.py -v"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} pytest not installed - skipping unit tests"
    echo "   Install with: pip install -r requirements-dev.txt"
fi

# Cleanup
echo ""
echo "🧹 Cleaning up test files..."
rm -f test-http.yaml test-tls.yaml test-failed.yaml
rm -f test-http-adv.yaml test-tls-adv.yaml test-failed-adv.yaml

echo ""
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  • Run unit tests: pytest tests/ -v"
echo "  • Test your own Ingress: ./migrate.py -i your-ingress.yaml -g your-gateway"
echo "  • Read documentation: cat docs/MIGRATION_GUIDE.md"
echo ""
echo "🤖 This tool was developed with Claude AI assistance for rapid deployment."
