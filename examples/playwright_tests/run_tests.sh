#!/bin/bash
#
# Quick start script for running Playwright tests with QAStudio reporter
#
# Usage:
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh --headed           # Run with visible browser
#   ./run_tests.sh --debug            # Run with Playwright inspector
#

set -e

# ============================================================================
# CONFIGURATION - Set your QAStudio.dev credentials here
# ============================================================================
# Uncomment and fill in your credentials to enable QAStudio reporter
# You can get these from https://qastudio.dev/settings

# export QASTUDIO_API_KEY="your_api_key_here"
# export QASTUDIO_PROJECT_ID="your_project_id_here"

# Optional configuration
# export QASTUDIO_ENVIRONMENT="local"          # e.g., local, staging, production
# export QASTUDIO_TEST_RUN_NAME="My Test Run"  # Custom test run name
# export QASTUDIO_VERBOSE="true"               # Enable verbose logging

# ============================================================================

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}QAStudio Playwright Test Runner${NC}"
echo "=================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating a virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
fi

# Check if playwright is installed
if ! command -v playwright &> /dev/null; then
    echo -e "${YELLOW}Playwright CLI not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
    playwright install chromium
    echo ""
fi

# Check for QAStudio credentials
if [ -n "$QASTUDIO_API_KEY" ] && [ -n "$QASTUDIO_PROJECT_ID" ]; then
    echo -e "${GREEN}✓${NC} QAStudio reporter enabled"
    echo "  API Key: ${QASTUDIO_API_KEY:0:10}..."
    echo "  Project ID: $QASTUDIO_PROJECT_ID"
    echo ""
else
    echo -e "${YELLOW}ℹ${NC} QAStudio reporter disabled (no credentials)"
    echo "  To enable, set environment variables:"
    echo "    export QASTUDIO_API_KEY=\"your_key\""
    echo "    export QASTUDIO_PROJECT_ID=\"your_project\""
    echo ""
fi

# Create artifact directories
mkdir -p screenshots traces videos

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo ""

pytest "$@"

EXIT_CODE=$?

# Summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Tests completed successfully${NC}"
else
    echo -e "${RED}✗ Tests failed with exit code $EXIT_CODE${NC}"
fi

# Show artifacts
if [ -d "traces" ] && [ "$(ls -A traces 2>/dev/null)" ]; then
    echo ""
    echo "Trace files saved to: traces/"
    echo "View traces with: playwright show-trace traces/<file>.zip"
fi

if [ -d "screenshots" ] && [ "$(ls -A screenshots 2>/dev/null)" ]; then
    echo "Screenshots saved to: screenshots/"
fi

exit $EXIT_CODE
