#!/bin/bash

# Frontend Test Runner
# This script runs all frontend tests with various options

set -e  # Exit on any error

echo "🧪 Starting Frontend Tests..."

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

# Function to run tests with coverage
run_tests_with_coverage() {
    echo "📊 Running tests with coverage..."
    npm test -- --coverage --watchAll=false --collectCoverageFrom='src/**/*.{ts,tsx}' --collectCoverageFrom='!src/**/*.d.ts' --collectCoverageFrom='!src/index.tsx' --collectCoverageFrom='!src/reportWebVitals.ts'
}

# Function to run tests in watch mode
run_tests_watch() {
    echo "👀 Running tests in watch mode..."
    npm test
}

# Function to run specific test files
run_specific_tests() {
    echo "🎯 Running specific tests: $1"
    npm test -- --testPathPattern="$1" --watchAll=false
}

# Function to run tests and generate HTML coverage report
run_tests_with_html_coverage() {
    echo "📈 Running tests with HTML coverage report..."
    npm test -- --coverage --watchAll=false --coverageReporters=html --collectCoverageFrom='src/**/*.{ts,tsx}' --collectCoverageFrom='!src/**/*.d.ts' --collectCoverageFrom='!src/index.tsx' --collectCoverageFrom='!src/reportWebVitals.ts'
}

# Parse command line arguments
case "${1:-default}" in
    "coverage")
        run_tests_with_coverage
        ;;
    "watch")
        run_tests_watch
        ;;
    "html")
        run_tests_with_html_coverage
        echo "📋 Coverage report generated in coverage/lcov-report/index.html"
        ;;
    "specific")
        if [ -z "$2" ]; then
            echo "❌ Error: Please provide a test pattern"
            echo "Usage: ./test-runner.sh specific <test-pattern>"
            exit 1
        fi
        run_specific_tests "$2"
        ;;
    "components")
        run_specific_tests "components"
        ;;
    "pages")
        run_specific_tests "pages"
        ;;
    "utils")
        run_specific_tests "utils"
        ;;
    "store")
        run_specific_tests "store"
        ;;
    "help")
        echo "Frontend Test Runner Options:"
        echo "  default/coverage  - Run all tests with coverage"
        echo "  watch            - Run tests in watch mode"
        echo "  html             - Run tests with HTML coverage report"
        echo "  specific <pattern> - Run specific tests matching pattern"
        echo "  components       - Run component tests only"
        echo "  pages           - Run page tests only"
        echo "  utils           - Run utility tests only"
        echo "  store           - Run Redux store tests only"
        echo "  help            - Show this help message"
        ;;
    "default"|*)
        run_tests_with_coverage
        ;;
esac

echo "✅ Frontend tests completed!" 