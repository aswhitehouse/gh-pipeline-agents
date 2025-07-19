#!/bin/bash

echo "🚀 Simple DACP CLI Test"
echo "======================"

# Set demo API key if not set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set, using demo key..."
    export OPENAI_API_KEY="key"
fi

# Sample error log
ERROR_LOG="npm ERR! code ENOENT
npm ERR! syscall open  
npm ERR! path /workspace/package.json
npm ERR! errno -2
npm ERR! enoent ENOENT: no such file or directory, open 'package.json'
Build failed with exit code 1"

echo "📋 Running DACP workflow..."

# Run the DACP CLI command with verbose logging
dacp run workflow agents/github-actions-error-workflow.yaml \
  --workflow-name quick_error_analysis \
  --input job_name="build-test" \
  --input workflow_name="CI Pipeline" \
  --input raw_logs="$ERROR_LOG" \
  --input repository="myorg/myproject" \
  --input branch="main" \
  --input commit_sha="abc123def456" \
  --input pr_number="42" \
  --log-level DEBUG \
  --output cli_test_results.json

# Check if it worked
if [ $? -eq 0 ]; then
    echo "✅ CLI execution successful!"
    
    if [ -f "cli_test_results.json" ]; then
        echo "📊 Results saved to cli_test_results.json"
        echo "First 500 characters of results:"
        head -c 500 cli_test_results.json
        echo "..."
        echo ""
        echo "📋 Full results file saved as cli_test_results.json for inspection"
        
        # Don't clean up so we can inspect the results
        # rm cli_test_results.json
    else
        echo "⚠️  No results file generated"
    fi
else
    echo "❌ CLI execution failed!"
fi

echo ""
echo "🎯 That's it! No Python scripting needed."
echo "   Just use the DACP CLI directly." 