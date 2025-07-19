# 🧪 Testing Your Error Analysis Workflow

## 🎯 Overview
This guide helps you test your GitHub Actions error analysis workflow on your own repository before integrating it into other projects.

## 📋 Prerequisites
- ✅ Your repository has the error analysis workflow (`.github/error-analysis.yml`)
- ✅ You have an `OPENAI_API_KEY` secret configured in your repository
- ✅ You have GitHub CLI installed locally (optional, for monitoring)

## 🚀 Quick Test Setup

### 1. **Automatic Test (Recommended)**
```bash
# Run the test script
./test_gh_workflow.sh
```

This will:
- ✅ Commit any uncommitted changes
- ✅ Push to trigger the test workflow
- ✅ Show you monitoring commands

### 2. **Manual Test**
```bash
# Commit and push the test workflow
git add .
git commit -m "Add test failure workflow for error analysis testing"
git push origin main

# Or trigger manually via GitHub CLI
gh workflow run "Test Failure Workflow"
```

## 📊 What Happens During Testing

### **Step 1: Test Workflow Fails**
The `test-failure.yml` workflow will:
- ❌ Try to run `npm install` without a `package.json` (fails)
- ❌ Try to import a non-existent Python module (fails)
- ❌ Try to compile invalid Python code (fails)

### **Step 2: Error Analysis Triggers**
Your `error-analysis.yml` workflow will:
- ✅ Detect the failed workflow
- ✅ Download and analyze the failure logs
- ✅ Run your DACP agents to analyze the error
- ✅ Generate AI-powered recommendations
- ✅ Upload results as artifacts

## 🔍 Monitoring the Test

### **Via GitHub Web Interface:**
1. Go to your repository's **Actions** tab
2. You'll see two workflows running:
   - `Test Failure Workflow` (will fail)
   - `GitHub Actions Error Analysis` (will analyze the failure)

### **Via GitHub CLI:**
```bash
# List recent workflow runs
gh run list --limit 10

# View specific run details
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

## 📈 Expected Results

### **Test Workflow Output:**
```
❌ npm ERR! code ENOENT
❌ npm ERR! syscall open
❌ npm ERR! path /workspace/package.json
❌ npm ERR! errno -2
❌ npm ERR! enoent ENOENT: no such file or directory, open 'package.json'
```

### **Error Analysis Output:**
Your AI agents should identify:
- ✅ **Root Cause:** Missing `package.json` file
- ✅ **Error Category:** File Not Found / Dependency Error
- ✅ **Recommended Fix:** Create `package.json` file
- ✅ **Developer Message:** Clear explanation and next steps

## 🎯 Validation Checklist

After running the test, verify:

- [ ] **Test workflow fails** (expected)
- [ ] **Error analysis workflow triggers** automatically
- [ ] **Logs are downloaded** and processed
- [ ] **DACP agents run** successfully
- [ ] **Analysis results** are generated
- [ ] **Artifacts are uploaded** (`analysis-results.json`)
- [ ] **No errors** in the error analysis workflow itself

## 🔧 Troubleshooting

### **If Error Analysis Doesn't Trigger:**
1. Check that `Test Failure Workflow` is in the trigger list
2. Verify the workflow name matches exactly
3. Check repository permissions

### **If Analysis Fails:**
1. Check `OPENAI_API_KEY` secret is configured
2. Verify DACP installation in the workflow
3. Check agent dependencies are installed

### **If Logs Are Empty:**
1. Check GitHub token permissions
2. Verify workflow run ID is accessible
3. Check log download step for errors

## 🚀 Next Steps

Once testing is successful:
1. **Remove test files** (optional, keep for future testing)
2. **Integrate into other projects** by copying the workflow
3. **Customize triggers** for your specific workflow names
4. **Adjust log processing** if needed for your use cases

## 📝 Test Workflow Details

The test workflow (`test-failure.yml`) creates realistic failures:
- **Build failure:** Missing `package.json` (common Node.js issue)
- **Python failure:** Import error (common dependency issue)
- **Lint failure:** Syntax error (common code quality issue)

This gives your AI agents a variety of error types to analyze! 