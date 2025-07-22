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

ROLE = "Github_Actions_Error_Remediator"

# Generate output models
class Propose_RemediationOutput(BaseModel):
    """Unified diff (patch) showing the proposed fix"""
    proposed_diff: str
    """List of files that should be changed"""
    files_to_change: List[str]
    """Explanation of why this fix is proposed"""
    rationale: str


# Task functions

def parse_propose_remediation_output(response) -> Propose_RemediationOutput:
    """Parse LLM response into Propose_RemediationOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Propose_RemediationOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Propose_RemediationOutput):
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
            "proposed_diff": "unified_default",
            "files_to_change": [],
            "rationale": "explanation_default"
        }
        result = parse_with_fallback(
            response=response,
            model_class=Propose_RemediationOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Propose a code change (diff) to fix the error described in the analyzer output.",
    role="executor",
    behavioural_flags={"conservatism": "moderate", "verbosity": "concise"},
    response_contract={"output_format": {"required_fields": ["proposed_diff", "files_to_change", "rationale"]}}
)
def propose_remediation(analysis_result: Dict[str, Any], raw_logs: str, repository: str, branch: str, commit_sha: str, memory_summary: str = '') -> Propose_RemediationOutput:
    """Process propose_remediation task.

    Args:
        analysis_result: {'type': 'object', 'description': 'Output from the analyzer agent (root cause, recommended fix, etc.)'}
        raw_logs: {'type': 'string', 'description': 'Raw logs from the failed workflow'}
        repository: {'type': 'string', 'description': 'Repository name (e.g., owner/repo)'}
        branch: {'type': 'string', 'description': 'Branch where the error occurred'}
        commit_sha: {'type': 'string', 'description': 'Commit SHA of the failed run'}
        memory_summary: Optional memory context for the task

    Returns:
        Propose_RemediationOutput
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
- proposed_diff (required): string
  Unified diff (patch) showing the proposed fix
- files_to_change (required): array of strings
  List of files that should be changed
- rationale (required): string
  Explanation of why this fix is proposed
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"propose_remediation.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "analysis_result": analysis_result, "raw_logs": raw_logs, "repository": repository, "branch": branch, "commit_sha": commit_sha
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
    "model": "gpt-4",
    "endpoint": "https://api.openai.com/v1",
    "temperature": 0.2,
    "max_tokens": 2000
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_propose_remediation_output(result)



class GithubActionsErrorRemediatorAgent(dacp.Agent):
    def __init__(self, agent_id: str, orchestrator: Orchestrator):
        super().__init__()
        self.agent_id = agent_id
        orchestrator.register_agent(agent_id, self)
        self.model = "gpt-4"

        # Embed YAML config as dict during generation
        self.config = {
            "logging": {
                "enabled": True,
                "level": "INFO",
                "format_style": "emoji",
                "include_timestamp": True,
                "log_file": "./logs/github-actions-remediator.log",
                "env_overrides": {
                    "level": "DACP_LOG_LEVEL",
                    "format_style": "DACP_LOG_STYLE",
                    "log_file": "DACP_LOG_FILE_REMEDIATOR"
                }
            },
            "intelligence": {
                "engine": "openai",
                "model": "gpt-4",
                "endpoint": "https://api.openai.com/v1",
                "config": {
                    "temperature": 0.2,
                    "max_tokens": 2000
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
                return result.model_dump()
            else:
                return result

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



    def propose_remediation(self, analysis_result, raw_logs, repository, branch, commit_sha) -> Propose_RemediationOutput:
        """Process propose_remediation task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return propose_remediation(analysis_result, raw_logs, repository, branch, commit_sha, memory_summary=memory_summary)



def main():
    # Example usage - in production, you would get these from your orchestrator setup
    from dacp.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    agent = GithubActionsErrorRemediatorAgent("example-agent-id", orchestrator)

    # Example usage with propose_remediation task: propose_remediation
    result = agent.propose_remediation(analysis_result="example_analysis_result", raw_logs="example_raw_logs", repository="example_repository", branch="example_branch", commit_sha="example_commit_sha")
    # Handle both Pydantic models and dictionaries
    if hasattr(result, 'model_dump'):
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()