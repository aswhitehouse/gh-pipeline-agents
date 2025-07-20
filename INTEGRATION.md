# GitHub Actions Error Analysis - Integration Guide

This guide shows how to integrate AI-powered error analysis into your GitHub repositories.

## 🚀 Quick Start

### Option 1: Use the Reusable Action (Recommended)

Add this to your repository's `.github/workflows/error-analysis.yml`:

```yaml
name: Error Analysis

on:
  workflow_run:
    workflows: ["CI", "Build", "Test", "Deploy"]  # Add your workflow names
    types: [completed]

jobs:
  analyze-error:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      actions: read
      pull-requests: write
    
    steps:
      - name: Run AI Error Analysis
        uses: aswhitehouse/gh-pipeline-agents@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          workflow_run_id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          branch: ${{ github.event.workflow_run.head_branch }}
          commit_sha: ${{ github.event.workflow_run.head_sha }}
          pr_number: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
```

### Option 2: Copy the Workflow

Copy the complete workflow from this repository:
- Copy `.github/workflows/error-analysis.yml` to your repo
- Copy the `agents/` directory to your repo
- Add your `OPENAI_API_KEY` secret

## 🔧 Setup Requirements

### 1. OpenAI API Key
Add your OpenAI API key as a repository secret:
- Go to your repository Settings → Secrets and variables → Actions
- Add a new secret named `OPENAI_API_KEY`
- Paste your OpenAI API key

### 2. Slack Webhook (Optional)
To enable Slack notifications:
- Go to your Slack workspace
- Create a new app or use an existing one
- Add the "Incoming Webhooks" feature
- Create a webhook for your desired channel (the webhook URL contains the channel info)
- Copy the webhook URL
- Add it as a repository secret named `SLACK_WEBHOOK_URL`

### 2. Permissions
The workflow needs these permissions:
- `contents: read` - To access repository files
- `actions: read` - To download workflow logs
- `pull-requests: write` - To comment on PRs (optional)

### 3. Workflow Triggers
Configure which workflows should trigger error analysis:
```yaml
on:
  workflow_run:
    workflows: ["CI", "Build", "Test", "Deploy"]  # Your workflow names
    types: [completed]
```

## 📋 Usage Examples

### Basic Integration
```yaml
# .github/workflows/error-analysis.yml
name: Error Analysis

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  analyze-error:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      actions: read
    steps:
      - uses: aswhitehouse/gh-pipeline-agents@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          workflow_run_id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
```

### With PR Comments
```yaml
# .github/workflows/error-analysis.yml
name: Error Analysis

on:
  workflow_run:
    workflows: ["CI", "Build"]
    types: [completed]

jobs:
  analyze-error:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      actions: read
      pull-requests: write
    steps:
      - uses: aswhitehouse/gh-pipeline-agents@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          workflow_run_id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          pr_number: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
```

### With Slack Notifications
```yaml
# .github/workflows/error-analysis.yml
name: Error Analysis

on:
  workflow_run:
    workflows: ["CI", "Build", "Deploy"]
    types: [completed]

jobs:
  analyze-error:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      actions: read
      pull-requests: write
    steps:
      - uses: aswhitehouse/gh-pipeline-agents@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          workflow_run_id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.repository }}
          branch: ${{ github.event.workflow_run.head_branch }}
          commit_sha: ${{ github.event.workflow_run.head_sha }}
          pr_number: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
          slack_webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
          # slack_channel: '#ci-alerts'  # Optional - webhook URL contains the channel
```

## 🔍 What You'll Get

### Analysis Results
- **Root Cause Analysis** - Identifies the primary error
- **Error Category** - Classifies the type of failure
- **Confidence Level** - How certain the analysis is
- **Impact Assessment** - Severity of the issue

### Recommended Fixes
- **Specific Actions** - What to do to fix the issue
- **Code Changes** - Files and changes needed
- **Commands to Run** - Terminal commands to execute
- **Prerequisites** - What you need before fixing

### Developer Messages
- **Clear Summary** - What went wrong
- **Detailed Explanation** - Why it happened
- **Next Steps** - What to do next
- **Prevention Tips** - How to avoid it in the future

## 🛡️ Security Considerations

### Data Privacy
- Logs are processed by OpenAI for analysis
- Sensitive data (passwords, tokens, URLs) is automatically redacted
- No logs are permanently stored

### Best Practices
- Don't log sensitive information in your workflows
- Use GitHub Secrets for API keys and passwords
- Review what gets logged before enabling analysis

## 🎯 Customization

### Modify Error Patterns
Edit the log processing to look for different error patterns:
```bash
grep -q -i "error\|fail\|exception\|fatal\|panic\|abort\|timeout\|oom" "$logfile"
```

### Add Custom Analysis
Extend the agents in the `agents/` directory to add your own analysis logic.

### Filter Workflows
Only analyze specific workflows by modifying the trigger:
```yaml
workflows: ["CI", "Build"]  # Only these workflows
```

## 🚨 Troubleshooting

### Common Issues

**"Log download failed"**
- Check that the workflow has `actions: read` permission
- Ensure the workflow run ID is correct
- Verify the repository name format (owner/repo)

**"Analysis failed"**
- Check your OpenAI API key is valid
- Ensure you have sufficient OpenAI credits
- Verify the agents directory is present

**"No error patterns found"**
- The logs might not contain obvious error keywords
- Check the uploaded artifacts for the raw logs
- Consider adding more error patterns

### Getting Help
- Check the workflow artifacts for detailed logs
- Review the GitHub Actions run logs
- Open an issue in this repository

## 📈 Advanced Usage

### Organization-Wide Integration
For multiple repositories in an organization:
1. Create a shared workflow in `.github` repository
2. Use organization secrets for OpenAI API key
3. Configure organization-wide workflow permissions

### Custom Error Analysis
Extend the system by:
1. Adding new agents to the `agents/` directory
2. Creating custom workflow definitions
3. Implementing domain-specific error patterns

### Integration with Other Tools
- **Slack Notifications** - Send analysis results to Slack
- **Jira Integration** - Create tickets from analysis results
- **Email Alerts** - Send critical error analysis via email 