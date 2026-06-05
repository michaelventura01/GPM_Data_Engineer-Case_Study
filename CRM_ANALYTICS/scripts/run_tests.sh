#!/bin/bash

echo "========================================="
echo "CRM ANALYTICS - TEST SUITE"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests based on argument
case "${1}" in
    "unit")
        echo -e "\n${YELLOW}Running unit tests...${NC}"
        pytest tests/unit/ -v
        ;;
    "integration")
        echo -e "\n${YELLOW}Running integration tests...${NC}"
        pytest tests/integration/ -v
        ;;
    "database")
        echo -e "\n${YELLOW}Running database tests...${NC}"
        pytest tests/integration/test_data_quality.py -v
        ;;
    "pipeline")
        echo -e "\n${YELLOW}Running pipeline tests...${NC}"
        pytest tests/integration/test_pipeline.py -v
        ;;
    "all")
        echo -e "\n${YELLOW}Running all tests...${NC}"
        pytest tests/ -v --cov=scripts --cov-report=html
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo -e "\n${YELLOW}Running quick tests...${NC}"
        pytest tests/unit/test_connections.py tests/unit/test_scripts.py -v
        ;;
    "watch")
        echo -e "\n${YELLOW}Running tests in watch mode...${NC}"
        pytest-watch -- tests/
        ;;
    *)
        echo "Usage: ./scripts/run_tests.sh [unit|integration|database|pipeline|all|quick|watch]"
        echo ""
        echo "Examples:"
        echo "  ./scripts/run_tests.sh unit        - Run only unit tests"
        echo "  ./scripts/run_tests.sh integration - Run integration tests"
        echo "  ./scripts/run_tests.sh all         - Run all tests"
        echo "  ./scripts/run_tests.sh quick       - Run quick tests"
        echo "  ./scripts/run_tests.sh watch       - Run tests on file changes"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✓ Tests completed${NC}"