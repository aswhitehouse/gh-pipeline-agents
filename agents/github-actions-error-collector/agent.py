import os
import logging
import json
from pathlib import Path
from typing import Optional, Any, Dict, List
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from behavioural_contracts import behavioural_contract
from dotenv import load_dotenv

import dacp
from dacp import parse_with_fallback, invoke_intelligence
from dacp.orchestrator import Orchestrator

load_dotenv()

log = logging.getLogger(__name__)

ROLE = "Github_Actions_Error_Collector"

# Generate output models
class Collect_ErrorsOutputError_Summary(BaseModel):
    """The main error message extracted from logs"""
    primary_error: str
    error_type: str
    severity: str
    """List of files mentioned in the error"""
    affected_files: Optional[List[str]] = None
    """Cleaned and formatted stack trace if available"""
    stack_trace: Optional[str] = None
    """Context around the error (before/after lines)"""
    error_context: Optional[str] = None
    """Keywords for further analysis"""
    suggested_keywords: Optional[List[str]] = None
class Collect_ErrorsOutputJob_Context(BaseModel):
    job_name: str
    workflow_name: str
    repository: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    failed_step: Optional[str] = None
class Collect_ErrorsOutputLog_Statistics(BaseModel):
    total_lines: int
    error_lines: int
    warning_lines: int
    """Estimated job duration before failure"""
    duration_estimate: Optional[str] = None
class Collect_ErrorsOutput(BaseModel):
    error_summary: Collect_ErrorsOutputError_Summary
    job_context: Collect_ErrorsOutputJob_Context
    log_statistics: Collect_ErrorsOutputLog_Statistics

class Extract_Build_InfoOutputEnvironment_Info(BaseModel):
    os: Optional[str] = None
    node_version: Optional[str] = None
    python_version: Optional[str] = None
    java_version: Optional[str] = None
class Extract_Build_InfoOutput(BaseModel):
    """Build commands that were executed"""
    build_commands: List[str]
    """Dependencies mentioned in the build"""
    dependencies: List[str]
    """Build artifacts that were expected"""
    build_artifacts: Optional[List[str]] = None
    """Environment information extracted from logs"""
    environment_info: Optional[Extract_Build_InfoOutputEnvironment_Info] = None


# Task functions

def parse_collect_errors_output(response) -> Collect_ErrorsOutput:
    """Parse LLM response into Collect_ErrorsOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Collect_ErrorsOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Collect_ErrorsOutput):
        return response

    # Parse JSON string if needed
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f'Failed to parse JSON response: {e}')

    # Use DACP's enhanced JSON parser with fallback support
    try:
        defaults = {
            "error_summary": {
                "primary_error": "default_primary_error",
                "error_type": "default_error_type",
                "severity": "default_severity",
                "affected_files": [],
                "stack_trace": "default_stack_trace",
                "error_context": "default_error_context",
                "suggested_keywords": []
            },
            "job_context": {
                "job_name": "default_job_name",
                "workflow_name": "default_workflow_name",
                "repository": "default_repository",
                "branch": "default_branch",
                "commit_sha": "default_commit_sha",
                "pr_number": 0,
                "failed_step": "default_failed_step"
            },
            "log_statistics": {
                "total_lines": 0,
                "error_lines": 0,
                "warning_lines": 0,
                "duration_estimate": "default_duration_estimate"
            }
        }
        result = parse_with_fallback(
            response=response,
            model_class=Collect_ErrorsOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Extract and summarize errors from GitHub Actions logs",
    role="analyst",
    behavioural_flags={"conservatism": "high", "verbosity": "detailed"},
    response_contract={"output_format": {"required_fields": ["error_summary", "job_context", "log_statistics"]}}
)
def collect_errors(job_name: str, workflow_name: str, raw_logs: str, job_step: str, repository: str, branch: str, commit_sha: str, pr_number: int, memory_summary: str = '') -> Collect_ErrorsOutput:
    """Process collect_errors task.

    Args:
        job_name: {'type': 'string', 'description': 'Name of the GitHub Actions job that failed', 'minLength': 1, 'maxLength': 200}
        workflow_name: {'type': 'string', 'description': 'Name of the GitHub Actions workflow', 'minLength': 1, 'maxLength': 200}
        raw_logs: {'type': 'string', 'description': 'Raw log output from the failed GitHub Actions job', 'minLength': 10, 'maxLength': 50000}
        job_step: {'type': 'string', 'description': 'Specific step in the job where the error occurred', 'maxLength': 500}
        repository: {'type': 'string', 'description': 'Repository where the workflow is running', 'pattern': '^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'}
        branch: {'type': 'string', 'description': 'Branch where the workflow was triggered', 'maxLength': 100}
        commit_sha: {'type': 'string', 'description': 'Commit SHA that triggered the workflow', 'pattern': '^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$'}
        pr_number: {'type': 'integer', 'description': 'Pull request number if applicable', 'minimum': 1}
        memory_summary: Optional memory context for the task

    Returns:
        Collect_ErrorsOutput
    """
    # Define memory configuration
    memory_config = {
        "enabled": False,
        "format": "string",
        "usage": "prompt-append",
        "required": False,
        "description": ""
    }

    # Define output format description
    output_format = """
- error_summary (required): object
  - primary_error (required): string
    The main error message extracted from logs
  - error_type (required): string
  - severity (required): string
  - affected_files (optional): array of strings
    List of files mentioned in the error
  - stack_trace (optional): string
    Cleaned and formatted stack trace if available
  - error_context (optional): string
    Context around the error (before/after lines)
  - suggested_keywords (optional): array of strings
    Keywords for further analysis
- job_context (required): object
  - job_name (required): string
  - workflow_name (required): string
  - repository (required): string
  - branch (optional): string
  - commit_sha (optional): string
  - pr_number (optional): integer
  - failed_step (optional): string
- log_statistics (required): object
  - total_lines (required): integer
  - error_lines (required): integer
  - warning_lines (required): integer
  - duration_estimate (optional): string
    Estimated job duration before failure
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"collect_errors.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "job_name": job_name, "workflow_name": workflow_name, "raw_logs": raw_logs, "job_step": job_step, "repository": repository, "branch": branch, "commit_sha": commit_sha, "pr_number": pr_number
    }

    # Render the prompt with all necessary context - pass variables directly for template access
    prompt = template.render(
        input=input_dict,
        memory_summary=memory_summary if memory_config['enabled'] else '',
        output_format=output_format,
        memory_config=memory_config,
        **input_dict  # Also pass variables directly for template access
    )

    # Configure intelligence for DACP
    intelligence_config = {
    "engine": "openai",
    "model": "gpt-3.5-turbo",
    "endpoint": "https://api.openai.com/v1",
    "temperature": 0.2,
    "max_tokens": 1500
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_collect_errors_output(result)


def parse_extract_build_info_output(response) -> Extract_Build_InfoOutput:
    """Parse LLM response into Extract_Build_InfoOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Extract_Build_InfoOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Extract_Build_InfoOutput):
        return response

    # Parse JSON string if needed
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f'Failed to parse JSON response: {e}')

    # Use DACP's enhanced JSON parser with fallback support
    try:
        defaults = {
            "build_commands": [],
            "dependencies": [],
            "build_artifacts": [],
            "environment_info": {
                "os": "default_os",
                "node_version": "default_node_version",
                "python_version": "default_python_version",
                "java_version": "default_java_version"
            }
        }
        result = parse_with_fallback(
            response=response,
            model_class=Extract_Build_InfoOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Extract build-specific information from logs",
    role="analyst",
    behavioural_flags={"conservatism": "high", "verbosity": "detailed"},
    response_contract={"output_format": {"required_fields": ["build_commands", "dependencies"]}}
)
def extract_build_info(raw_logs: str, build_system: str, memory_summary: str = '') -> Extract_Build_InfoOutput:
    """Process extract_build_info task.

    Args:
        raw_logs: {'type': 'string', 'description': 'Raw log output to analyze for build information'}
        build_system: {'type': 'string', 'enum': ['npm', 'maven', 'gradle', 'docker', 'python', 'rust', 'go', 'other'], 'description': 'Type of build system used'}
        memory_summary: Optional memory context for the task

    Returns:
        Extract_Build_InfoOutput
    """
    # Define memory configuration
    memory_config = {
        "enabled": False,
        "format": "string",
        "usage": "prompt-append",
        "required": False,
        "description": ""
    }

    # Define output format description
    output_format = """
- build_commands (required): array of strings
  Build commands that were executed
- dependencies (required): array of strings
  Dependencies mentioned in the build
- build_artifacts (optional): array of strings
  Build artifacts that were expected
- environment_info (optional): object
  Environment information extracted from logs
  - os (optional): string
  - node_version (optional): string
  - python_version (optional): string
  - java_version (optional): string
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"extract_build_info.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "raw_logs": raw_logs, "build_system": build_system
    }

    # Render the prompt with all necessary context - pass variables directly for template access
    prompt = template.render(
        input=input_dict,
        memory_summary=memory_summary if memory_config['enabled'] else '',
        output_format=output_format,
        memory_config=memory_config,
        **input_dict  # Also pass variables directly for template access
    )

    # Configure intelligence for DACP
    intelligence_config = {
    "engine": "openai",
    "model": "gpt-3.5-turbo",
    "endpoint": "https://api.openai.com/v1",
    "temperature": 0.2,
    "max_tokens": 1500
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_extract_build_info_output(result)



class GithubActionsErrorCollectorAgent(dacp.Agent):
    def __init__(self, agent_id: str, orchestrator: Orchestrator):
        super().__init__()
        self.agent_id = agent_id
        orchestrator.register_agent(agent_id, self)
        self.model = "gpt-3.5-turbo"

        # Embed YAML config as dict during generation
        self.config = {
            "logging": {
                "enabled": True,
                "level": "INFO",
                "format_style": "emoji",
                "include_timestamp": True,
                "log_file": "./logs/github-actions-collector.log",
                "env_overrides": {
                    "level": "DACP_LOG_LEVEL",
                    "format_style": "DACP_LOG_STYLE",
                    "log_file": "DACP_LOG_FILE_COLLECTOR"
                }
            },
            "intelligence": {
                "engine": "openai",
                "model": "gpt-3.5-turbo",
                "endpoint": "https://api.openai.com/v1",
                "config": {
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
            }
        }

        # Setup DACP logging FIRST
        self.setup_logging()


    def handle_message(self, message: dict) -> dict:
        """
        Handles incoming messages from the orchestrator.
        Processes messages based on the task specified and routes to appropriate agent methods.
        """
        task = message.get("task")
        if not task:
            return {"error": "Missing required field: task"}

        # Map task names to method names (replace hyphens with underscores)
        method_name = task.replace("-", "_")

        # Check if the method exists on this agent
        if not hasattr(self, method_name):
            return {"error": f"Unknown task: {task}"}

        try:
            # Get the method and extract its parameters (excluding 'self')
            method = getattr(self, method_name)

            # Call the method with the message parameters (excluding 'task')
            method_params = {k: v for k, v in message.items() if k != "task"}
            result = method(**method_params)

            # Handle both Pydantic models and dictionaries
            if hasattr(result, 'model_dump'):
                return json.dumps(result.model_dump())
            else:
                return json.dumps(result)

        except TypeError as e:
            return {"error": f"Invalid parameters for task {task}: {str(e)}"}
        except Exception as e:
            return {"error": f"Error executing task {task}: {str(e)}"}



    def setup_logging(self):
        """Configure DACP logging from YAML configuration."""
        logging_config = self.config.get('logging', {})

        if not logging_config.get('enabled', True):
            return

        # Process environment variable overrides
        env_overrides = logging_config.get('env_overrides', {})

        level = logging_config.get('level', 'INFO')
        if 'level' in env_overrides:
            level = os.getenv(env_overrides['level'], level)

        format_style = logging_config.get('format_style', 'emoji')
        if 'format_style' in env_overrides:
            format_style = os.getenv(env_overrides['format_style'], format_style)

        log_file = logging_config.get('log_file')
        if 'log_file' in env_overrides:
            log_file = os.getenv(env_overrides['log_file'], log_file)

        # Create log directory if needed
        if log_file:
            from pathlib import Path
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Configure DACP logging
        dacp.setup_dacp_logging(
            level=level,
            format_style=format_style,
            include_timestamp=logging_config.get('include_timestamp', True),
            log_file=log_file
        )



    def collect_errors(self, job_name, workflow_name, raw_logs, job_step, repository, branch, commit_sha, pr_number) -> Collect_ErrorsOutput:
        """Process collect_errors task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return collect_errors(job_name, workflow_name, raw_logs, job_step, repository, branch, commit_sha, pr_number, memory_summary=memory_summary)


    def extract_build_info(self, raw_logs, build_system) -> Extract_Build_InfoOutput:
        """Process extract_build_info task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return extract_build_info(raw_logs, build_system, memory_summary=memory_summary)



def main():
    # Example usage - in production, you would get these from your orchestrator setup
    from dacp.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    agent = GithubActionsErrorCollectorAgent("example-agent-id", orchestrator)

    # Example usage with collect_errors task: collect_errors
    result = agent.collect_errors(job_name="example_job_name", workflow_name="example_workflow_name", raw_logs="example_raw_logs", job_step="example_job_step", repository="example_repository", branch="example_branch", commit_sha="example_commit_sha", pr_number="example_pr_number")
    # Handle both Pydantic models and dictionaries
    if hasattr(result, 'model_dump'):
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()