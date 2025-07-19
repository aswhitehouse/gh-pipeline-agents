# Github Actions Error Collector

Agent that collects and summarizes errors from GitHub Actions job logs and stack traces

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py
```

## Tasks

### Collect_Errors

Extract and summarize errors from GitHub Actions logs

#### Input:
- type: object
- properties: {'job_name': {'type': 'string', 'description': 'Name of the GitHub Actions job that failed', 'minLength': 1, 'maxLength': 200}, 'workflow_name': {'type': 'string', 'description': 'Name of the GitHub Actions workflow', 'minLength': 1, 'maxLength': 200}, 'raw_logs': {'type': 'string', 'description': 'Raw log output from the failed GitHub Actions job', 'minLength': 10, 'maxLength': 50000}, 'job_step': {'type': 'string', 'description': 'Specific step in the job where the error occurred', 'maxLength': 500}, 'repository': {'type': 'string', 'description': 'Repository where the workflow is running', 'pattern': '^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'}, 'branch': {'type': 'string', 'description': 'Branch where the workflow was triggered', 'maxLength': 100}, 'commit_sha': {'type': 'string', 'description': 'Commit SHA that triggered the workflow', 'pattern': '^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$'}, 'pr_number': {'type': 'integer', 'description': 'Pull request number if applicable', 'minimum': 1}}
- required: ['job_name', 'workflow_name', 'raw_logs', 'repository']

#### Output:
- type: object
- properties: {'error_summary': {'type': 'object', 'properties': {'primary_error': {'type': 'string', 'description': 'The main error message extracted from logs'}, 'error_type': {'type': 'string', 'enum': ['build_failure', 'test_failure', 'dependency_error', 'syntax_error', 'runtime_error', 'timeout', 'permission_error', 'network_error', 'configuration_error', 'deployment_error', 'linting_error', 'other']}, 'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}, 'affected_files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of files mentioned in the error'}, 'stack_trace': {'type': 'string', 'description': 'Cleaned and formatted stack trace if available'}, 'error_context': {'type': 'string', 'description': 'Context around the error (before/after lines)'}, 'suggested_keywords': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Keywords for further analysis'}}, 'required': ['primary_error', 'error_type', 'severity']}, 'job_context': {'type': 'object', 'properties': {'job_name': {'type': 'string'}, 'workflow_name': {'type': 'string'}, 'repository': {'type': 'string'}, 'branch': {'type': 'string'}, 'commit_sha': {'type': 'string'}, 'pr_number': {'type': 'integer'}, 'failed_step': {'type': 'string'}}, 'required': ['job_name', 'workflow_name', 'repository']}, 'log_statistics': {'type': 'object', 'properties': {'total_lines': {'type': 'integer'}, 'error_lines': {'type': 'integer'}, 'warning_lines': {'type': 'integer'}, 'duration_estimate': {'type': 'string', 'description': 'Estimated job duration before failure'}}, 'required': ['total_lines', 'error_lines', 'warning_lines']}}
- required: ['error_summary', 'job_context', 'log_statistics']

### Extract_Build_Info

Extract build-specific information from logs

#### Input:
- type: object
- properties: {'raw_logs': {'type': 'string', 'description': 'Raw log output to analyze for build information'}, 'build_system': {'type': 'string', 'enum': ['npm', 'maven', 'gradle', 'docker', 'python', 'rust', 'go', 'other'], 'description': 'Type of build system used'}}
- required: ['raw_logs']

#### Output:
- type: object
- properties: {'build_commands': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Build commands that were executed'}, 'dependencies': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Dependencies mentioned in the build'}, 'build_artifacts': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Build artifacts that were expected'}, 'environment_info': {'type': 'object', 'properties': {'os': {'type': 'string'}, 'node_version': {'type': 'string'}, 'python_version': {'type': 'string'}, 'java_version': {'type': 'string'}}, 'description': 'Environment information extracted from logs'}}
- required: ['build_commands', 'dependencies']


## Behavioural Contract


This agent is governed by the following behavioural contract policy:



Refer to `behavioural_contracts` for enforcement logic.


## Example Usage

```python
from agent import GithubActionsErrorCollector

agent = GithubActionsErrorCollector()
# Example usage
task_name = "collect_errors"
if task_name:
    result = getattr(agent, task_name.replace("-", "_"))(
        type="example_type", properties="example_properties", required="example_required"
    )
    print(result)
```
