# Testing Guide for GitHub Actions Error Analysis Multi-Agent System

This guide will help you test your multi-agent system locally before deploying to GitHub Actions.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git repository with your multi-agent system

## Quick Start

### 1. Setup Environment

Run the setup script to prepare your environment:

```bash
chmod +x setup_test_environment.sh
./setup_test_environment.sh
```

This script will:
- Check Python version
- Create a virtual environment
- Install base dependencies
- Create necessary directories
- Set up environment variables

### 2. Configure API Key

Edit the `.env` file and add your OpenAI API key:

```bash
# Edit .env file
nano .env

# Or set it directly in your shell
export OPENAI_API_KEY='your-openai-api-key-here'
```

### 3. Test with DACP CLI (Recommended - Matches GitHub Actions)

Test your agents using DACP's CLI commands, exactly as they'll run on GitHub Actions:

```bash
# Make the test script executable
chmod +x test_single_task.sh

# Test individual tasks
./test_single_task.sh

# Test complete workflow
python test_dacp_cli.py
```

This approach:
- ✅ Uses the same DACP CLI commands as GitHub Actions
- ✅ Tests real LLM API calls
- ✅ Validates agent specifications
- ✅ Ensures production-like behavior

### 4. Alternative: Run Simple Tests (No DACP Required)

If you don't have DACP installed yet, start with the simple test script:

```bash
python test_simple_agents.py
```

This will test:
- ✅ Agent module imports
- ✅ Prompt template loading
- ✅ Data structure definitions
- ✅ Workflow file validation
- ✅ GitHub Actions file validation
- ✅ Workflow simulation (without LLM calls)

### 5. Alternative: Run Full Tests (Requires DACP and behavioural-contracts)

If you have DACP and behavioural-contracts installed, run the full test:

```bash
python test_local_agents.py
```

This will test:
- ✅ Complete agent functionality
- ✅ Real LLM API calls
- ✅ End-to-end workflow execution
- ✅ Multiple test scenarios

## Test Scenarios

The test scripts include realistic GitHub Actions failure scenarios:

### 1. NPM Missing Package.json
- **Error**: `ENOENT: no such file or directory, open 'package.json'`
- **Type**: Dependency error
- **Expected Analysis**: Missing package.json file in repository root

### 2. Python Import Error
- **Error**: `ImportError: cannot import name 'register_assert_rewrite' from '_pytest.assertion'`
- **Type**: Import error
- **Expected Analysis**: Pytest version compatibility issue

### 3. Docker Build Failure
- **Error**: `ERROR: Could not open requirements file: requirements.txt`
- **Type**: Build error
- **Expected Analysis**: Missing requirements.txt in Docker context

## Understanding Test Results

### DACP CLI Test Output

```
GitHub Actions Error Analysis - Single Task Tester
==================================================
✅ DACP is installed
✅ OPENAI_API_KEY is set

Testing Collector Agent - collect_errors task
------------------------------------------------
Running: dacp task run --agent-spec agents/github-actions-error-collector.yaml --task collect_errors --input temp/collector_input.json --output temp/collector_output.json
✅ collect_errors task completed successfully

Output:
{
  "error_summary": {
    "primary_error": "ENOENT: no such file or directory, open 'package.json'",
    "error_type": "dependency_error",
    "severity": "high",
    "affected_files": ["package.json"],
    "stack_trace": null,
    "error_context": "npm install step",
    "suggested_keywords": ["package.json", "npm", "dependency"]
  },
  "job_context": {
    "job_name": "build-and-test",
    "workflow_name": "CI Pipeline",
    "repository": "myorg/myproject",
    "branch": "feature/new-feature",
    "commit_sha": "abc123def4567890abcdef1234567890abcdef12",
    "pr_number": 42,
    "failed_step": "npm install"
  },
  "log_statistics": {
    "total_lines": 8,
    "error_lines": 6,
    "warning_lines": 0,
    "duration_estimate": "30s"
  }
}

Testing Collector Agent - extract_build_info task
--------------------------------------------------------
Running: dacp task run --agent-spec agents/github-actions-error-collector.yaml --task extract_build_info --input temp/build_info_input.json --output temp/build_info_output.json
✅ extract_build_info task completed successfully

Testing Analyzer Agent - analyze_error task
-----------------------------------------------
Running: dacp task run --agent-spec agents/github-actions-error-analyzer.yaml --task analyze_error --input temp/analyze_input.json --output temp/analyze_output.json
✅ analyze_error task completed successfully

🎉 All single task tests completed successfully!
```

### Simple Test Output

```
GitHub Actions Error Analysis Multi-Agent System - Simple Local Test
======================================================================

Running: Agent Imports
----------------------------------------
✅ Agent Imports passed

Running: Prompt Templates
----------------------------------------
✅ Prompt Templates passed

Running: Data Structures
----------------------------------------
✅ Data Structures passed

Running: Workflow File
----------------------------------------
✅ Workflow File passed

Running: GitHub Actions Files
----------------------------------------
✅ GitHub Actions Files passed

Testing: Workflow Simulation (No LLM)
----------------------------------------
✅ Workflow simulation passed

======================================================================
FINAL TEST SUMMARY
======================================================================
Total tests: 6
Successful: 6
Failed: 0

🎉 All tests passed! Your multi-agent system structure is valid.
Next step: Install DACP and behavioural-contracts to test with real LLM calls.
```

### Full Test Output

```
GitHub Actions Error Analysis Multi-Agent System - Local Test
======================================================================

Testing: npm_missing_package_json
----------------------------------------
✅ Complete workflow test passed

============================================================
TEST SUMMARY: npm_missing_package_json
============================================================
Status: success
Steps completed: collect_errors, extract_build_info, analyze_error, generate_pr_comment, suggest_workflow_improvements

Collector Results:
  Primary Error: ENOENT: no such file or directory, open 'package.json'
  Error Type: dependency_error
  Severity: high

Analyzer Results:
  Root Cause: Missing package.json file in the repository
  Confidence: high
  Urgency: medium
  PR Comment Generated: Yes
============================================================

======================================================================
FINAL TEST SUMMARY
======================================================================
Total tests: 3
Successful: 3
Failed: 0

🎉 All tests passed! Your multi-agent system is ready for deployment.
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
✗ Import failed: No module named 'dacp'
```
**Solution**: Install DACP and behavioural-contracts, or use the simple test script first.

#### 2. API Key Issues
```
OPENAI_API_KEY not found in environment
```
**Solution**: Set your OpenAI API key in the `.env` file or environment variables.

#### 3. Permission Errors
```
Permission denied: setup_test_environment.sh
```
**Solution**: Make the script executable: `chmod +x setup_test_environment.sh`

#### 4. Python Version Issues
```
Python 3.8 or higher is required
```
**Solution**: Upgrade Python or use a different Python version.

### Debug Mode

To get more detailed output, set the log level:

```bash
export DACP_LOG_LEVEL=DEBUG
python test_simple_agents.py
```

### Viewing Logs

Check the log files for detailed information:

```bash
# Simple test logs
cat simple_test_run.log

# Full test logs
cat test_run.log

# Agent-specific logs
cat logs/collector.log
cat logs/analyzer.log
```

## Test Output Files

The test scripts generate several output files:

- `simple_test_results_*.json` - Results from simple tests
- `test_results_*.json` - Results from full tests
- `simple_test_run.log` - Simple test execution logs
- `test_run.log` - Full test execution logs
- `logs/collector.log` - Collector agent logs
- `logs/analyzer.log` - Analyzer agent logs

## Next Steps

After successful testing:

1. **Deploy to GitHub Actions**: Use the workflow files in your repository
2. **Monitor Performance**: Check the generated logs and metrics
3. **Iterate**: Use test results to improve agent prompts and logic
4. **Scale**: Add more test scenarios and edge cases

## Customizing Tests

### Adding New Test Cases

Edit the `TEST_CASES` dictionary in either test script:

```python
TEST_CASES = {
    "your_new_test": {
        "job_name": "your-job",
        "workflow_name": "Your Workflow",
        "raw_logs": """
        Your GitHub Actions log output here
        """,
        "repository": "yourorg/yourproject",
        "branch": "main",
        "commit_sha": "abc123...",
        "pr_number": 123,
        "job_step": "your-step"
    }
}
```

### Modifying Test Logic

The test functions can be customized to test specific aspects:

- `test_collector_agent()` - Test error collection
- `test_analyzer_agent()` - Test error analysis
- `test_complete_workflow()` - Test end-to-end workflow

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify your OpenAI API key is valid
3. Ensure all dependencies are installed
4. Check that your agent files are properly structured

For more help, refer to the agent-specific README files in the `agents/` directory. 