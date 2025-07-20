#!/bin/bash

# Quick setup script for GitHub Actions Error Analysis
# Run this in your repository to set up error analysis

echo "🚀 Setting up GitHub Actions Error Analysis..."

# Create workflows directory if it doesn't exist
mkdir -p .github/workflows

# Download the basic integration workflow
echo "📥 Downloading integration workflow..."
curl -o .github/workflows/error-analysis.yml \
  https://raw.githubusercontent.com/aswhitehouse/gh-pipeline-agents/main/examples/basic-integration.yml

# Create a simple test workflow to verify setup
echo "🧪 Creating test workflow..."
cat > .github/workflows/test-error-analysis.yml << 'EOF'
name: Test Error Analysis

on:
  workflow_dispatch:  # Manual trigger for testing

jobs:
  test-failure:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Intentionally fail
        run: |
          echo "This is a test failure to trigger error analysis"
          exit 1
EOF

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add your OpenAI API key as a repository secret:"
echo "   - Go to Settings → Secrets and variables → Actions"
echo "   - Add secret named 'OPENAI_API_KEY'"
echo "   - Paste your OpenAI API key"
echo ""
echo "2. Customize the workflow triggers in .github/workflows/error-analysis.yml:"
echo "   - Update the 'workflows' list to include your workflow names"
echo ""
echo "3. Test the setup:"
echo "   - Go to Actions → 'Test Error Analysis'"
echo "   - Click 'Run workflow' to trigger a test failure"
echo ""
echo "4. Check the results:"
echo "   - Look for the 'Error Analysis' workflow that triggers automatically"
echo "   - Review the analysis results and artifacts"
echo ""
echo "📚 For more information, see: https://github.com/aswhitehouse/gh-pipeline-agents/blob/main/INTEGRATION.md" 