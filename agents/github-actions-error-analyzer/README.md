# Github Actions Error Analyzer

Agent that analyzes collected GitHub Actions errors and provides developer-friendly explanations and fixes

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py
```

## Tasks

### Analyze_Error

Analyze structured error data and provide developer-friendly explanations

#### Input:
- type: object
- properties: {'error_summary': {'type': 'object', 'properties': {'primary_error': {'type': 'string', 'description': 'The main error message extracted from logs'}, 'error_type': {'type': 'string', 'enum': ['build_failure', 'test_failure', 'dependency_error', 'syntax_error', 'runtime_error', 'timeout', 'permission_error', 'network_error', 'configuration_error', 'deployment_error', 'linting_error', 'other']}, 'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}, 'affected_files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of files mentioned in the error'}, 'stack_trace': {'type': 'string', 'description': 'Cleaned and formatted stack trace if available'}, 'error_context': {'type': 'string', 'description': 'Context around the error (before/after lines)'}, 'suggested_keywords': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Keywords for further analysis'}}, 'required': ['primary_error', 'error_type', 'severity']}, 'job_context': {'type': 'object', 'properties': {'job_name': {'type': 'string'}, 'workflow_name': {'type': 'string'}, 'repository': {'type': 'string'}, 'branch': {'type': 'string'}, 'commit_sha': {'type': 'string'}, 'pr_number': {'type': 'integer'}, 'failed_step': {'type': 'string'}}, 'required': ['job_name', 'workflow_name', 'repository']}, 'log_statistics': {'type': 'object', 'properties': {'total_lines': {'type': 'integer'}, 'error_lines': {'type': 'integer'}, 'warning_lines': {'type': 'integer'}, 'duration_estimate': {'type': 'string', 'description': 'Estimated job duration before failure'}}, 'required': ['total_lines', 'error_lines', 'warning_lines']}, 'additional_context': {'type': 'object', 'properties': {'recent_changes': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Recent file changes or commits'}, 'build_commands': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Build commands that were executed'}, 'dependencies': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Dependencies mentioned in the build'}, 'environment_info': {'type': 'object', 'description': 'Environment information'}}}}
- required: ['error_summary', 'job_context', 'log_statistics']

#### Output:
- type: object
- properties: {'analysis_result': {'type': 'object', 'properties': {'root_cause': {'type': 'string', 'description': 'Clear explanation of what caused the error'}, 'error_category': {'type': 'string', 'enum': ['configuration_issue', 'dependency_problem', 'code_issue', 'environment_issue', 'infrastructure_issue', 'permissions_issue', 'timing_issue', 'resource_issue']}, 'confidence_level': {'type': 'string', 'enum': ['low', 'medium', 'high', 'very_high'], 'description': 'Confidence in the root cause analysis'}, 'impact_assessment': {'type': 'string', 'description': 'Assessment of the impact on the development workflow'}}, 'required': ['root_cause', 'error_category', 'confidence_level', 'impact_assessment']}, 'recommended_fixes': {'type': 'array', 'items': {'type': 'object', 'properties': {'fix_title': {'type': 'string', 'description': 'Short title for the fix'}, 'fix_description': {'type': 'string', 'description': 'Detailed description of the fix'}, 'fix_type': {'type': 'string', 'enum': ['immediate', 'short_term', 'long_term']}, 'estimated_effort': {'type': 'string', 'enum': ['low', 'medium', 'high']}, 'code_changes': {'type': 'array', 'items': {'type': 'object', 'properties': {'file_path': {'type': 'string'}, 'suggested_change': {'type': 'string'}, 'change_type': {'type': 'string', 'enum': ['add', 'modify', 'remove', 'rename']}}}, 'description': 'Specific code changes needed'}, 'commands_to_run': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Commands to execute for the fix'}, 'prerequisites': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Prerequisites for this fix'}}, 'required': ['fix_title', 'fix_description', 'fix_type', 'estimated_effort']}, 'minItems': 1, 'maxItems': 5}, 'developer_message': {'type': 'object', 'properties': {'summary': {'type': 'string', 'description': 'Brief summary for the developer'}, 'detailed_explanation': {'type': 'string', 'description': 'Detailed explanation in developer-friendly language'}, 'next_steps': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Prioritized list of next steps'}, 'related_documentation': {'type': 'array', 'items': {'type': 'object', 'properties': {'title': {'type': 'string'}, 'url': {'type': 'string'}}, 'description': 'Links to relevant documentation'}}, 'prevention_tips': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Tips to prevent similar issues in the future'}}, 'required': ['summary', 'detailed_explanation', 'next_steps']}, 'urgency_level': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical'], 'description': 'How urgently this needs to be addressed'}}
- required: ['analysis_result', 'recommended_fixes', 'developer_message', 'urgency_level']

### Generate_Pr_Comment

Generate a formatted comment for posting to a GitHub PR

#### Input:
- type: object
- properties: {'analysis_result': {'type': 'object', 'description': 'The analysis result from analyze_error task'}, 'recommended_fixes': {'type': 'array', 'description': 'The recommended fixes from analyze_error task'}, 'developer_message': {'type': 'object', 'description': 'The developer message from analyze_error task'}, 'pr_number': {'type': 'integer', 'description': 'Pull request number'}, 'repository': {'type': 'string', 'description': 'Repository name'}, 'job_name': {'type': 'string', 'description': 'Failed job name'}, 'workflow_name': {'type': 'string', 'description': 'Workflow name'}}
- required: ['analysis_result', 'recommended_fixes', 'developer_message', 'pr_number', 'repository', 'job_name']

#### Output:
- type: object
- properties: {'pr_comment': {'type': 'string', 'description': 'Formatted markdown comment for GitHub PR'}, 'comment_metadata': {'type': 'object', 'properties': {'comment_type': {'type': 'string', 'enum': ['error_analysis', 'fix_suggestion', 'workflow_failure']}, 'tags': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Tags for categorizing the comment'}, 'urgency': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}}, 'required': ['comment_type', 'tags', 'urgency']}}
- required: ['pr_comment', 'comment_metadata']

### Suggest_Workflow_Improvements

Suggest improvements to the GitHub Actions workflow to prevent similar issues

#### Input:
- type: object
- properties: {'error_analysis': {'type': 'object', 'description': 'Previous analysis result'}, 'workflow_name': {'type': 'string', 'description': 'Name of the workflow'}, 'repository': {'type': 'string', 'description': 'Repository name'}, 'recurring_patterns': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Patterns of recurring issues'}}
- required: ['error_analysis', 'workflow_name', 'repository']

#### Output:
- type: object
- properties: {'workflow_improvements': {'type': 'array', 'items': {'type': 'object', 'properties': {'improvement_title': {'type': 'string'}, 'improvement_description': {'type': 'string'}, 'improvement_type': {'type': 'string', 'enum': ['error_handling', 'caching', 'parallelization', 'monitoring', 'configuration']}, 'implementation_difficulty': {'type': 'string', 'enum': ['easy', 'moderate', 'hard']}, 'expected_benefit': {'type': 'string', 'enum': ['low', 'medium', 'high']}, 'workflow_changes': {'type': 'string', 'description': 'Specific YAML changes needed'}}, 'required': ['improvement_title', 'improvement_description', 'improvement_type', 'implementation_difficulty', 'expected_benefit']}}, 'prevention_strategies': {'type': 'array', 'items': {'type': 'string'}, 'description': 'General strategies to prevent similar issues'}, 'monitoring_recommendations': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Recommendations for better monitoring'}}
- required: ['workflow_improvements', 'prevention_strategies', 'monitoring_recommendations']


## Behavioural Contract


This agent is governed by the following behavioural contract policy:



Refer to `behavioural_contracts` for enforcement logic.


## Example Usage

```python
from agent import GithubActionsErrorAnalyzer

agent = GithubActionsErrorAnalyzer()
# Example usage
task_name = "analyze_error"
if task_name:
    result = getattr(agent, task_name.replace("-", "_"))(
        type="example_type", properties="example_properties", required="example_required"
    )
    print(result)
```
