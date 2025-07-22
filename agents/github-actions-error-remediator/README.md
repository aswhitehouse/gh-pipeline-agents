# Github Actions Error Remediator

Agent that proposes code changes to remediate errors detected in GitHub Actions runs, based on analyzer output.

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py
```

## Tasks

### Propose_Remediation

Propose a code change (diff) to fix the error described in the analyzer output.

#### Input:
- type: object
- properties: {'analysis_result': {'type': 'object', 'description': 'Output from the analyzer agent (root cause, recommended fix, etc.)'}, 'raw_logs': {'type': 'string', 'description': 'Raw logs from the failed workflow'}, 'repository': {'type': 'string', 'description': 'Repository name (e.g., owner/repo)'}, 'branch': {'type': 'string', 'description': 'Branch where the error occurred'}, 'commit_sha': {'type': 'string', 'description': 'Commit SHA of the failed run'}}
- required: ['analysis_result', 'raw_logs', 'repository', 'branch', 'commit_sha']
- examples: [{'analysis_result': {'root_cause': 'Missing package.json file', 'recommended_fixes': ['Add a package.json file to the repository root']}, 'raw_logs': "npm ERR! enoent ENOENT: no such file or directory, open 'package.json'", 'repository': 'myorg/myrepo', 'branch': 'main', 'commit_sha': 'abc123def456'}]

#### Output:
- type: object
- properties: {'proposed_diff': {'type': 'string', 'description': 'Unified diff (patch) showing the proposed fix'}, 'files_to_change': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of files that should be changed'}, 'rationale': {'type': 'string', 'description': 'Explanation of why this fix is proposed'}}
- required: ['proposed_diff', 'files_to_change', 'rationale']
- examples: [{'proposed_diff': '--- /dev/null\n+++ b/package.json\n@@ ... (diff content here)\n', 'files_to_change': ['package.json'], 'rationale': 'The error indicates that package.json is missing. Adding this file resolves the npm error.'}]


## Behavioural Contract


This agent is governed by the following behavioural contract policy:



Refer to `behavioural_contracts` for enforcement logic.


## Example Usage

```python
from agent import GithubActionsErrorRemediator

agent = GithubActionsErrorRemediator()
# Example usage
task_name = "propose_remediation"
if task_name:
    result = getattr(agent, task_name.replace("-", "_"))(
        type="example_type", properties="example_properties", required="example_required", examples="example_examples"
    )
    print(result)
```
