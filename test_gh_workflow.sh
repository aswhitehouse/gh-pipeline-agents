#!/bin/bash

echo "🚀 GitHub Actions Error Analysis Test"
echo "====================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from your project root."
    exit 1
fi

# Check if we have the test file
if [ ! -f ".github/test-failure.yml" ]; then
    echo "❌ Test workflow file not found. Please ensure .github/test-failure.yml exists."
    exit 1
fi

echo "✅ Test workflow found: .github/test-failure.yml"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📋 Current branch: $CURRENT_BRANCH"

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes. Committing them first..."
    git add .
    git commit -m "Auto-commit before testing error analysis workflow"
fi

# Push to trigger the workflow
echo "🚀 Pushing to trigger test workflow..."
git push origin $CURRENT_BRANCH

echo ""
echo "📊 Workflow Status:"
echo "=================="
echo "1. Test workflow will start and fail (this is expected!)"
echo "2. Error analysis workflow will trigger automatically"
echo "3. Check the Actions tab in GitHub to monitor progress"
echo ""
echo "🔗 GitHub Actions URL:"
echo "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/')/actions"
echo ""
echo "📋 To monitor the workflow:"
echo "   gh run list --limit 5"
echo ""
echo "📋 To view specific run logs:"
echo "   gh run view <run-id>"
echo ""
echo "🎯 Expected behavior:"
echo "   ✅ Test workflow fails (npm install without package.json)"
echo "   ✅ Error analysis workflow triggers"
echo "   ✅ AI analyzes the failure and provides recommendations"
echo "   ✅ Results uploaded as artifacts"
echo ""
echo "💡 To trigger manually instead:"
echo "   gh workflow run 'Test Failure Workflow'" 