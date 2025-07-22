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

ROLE = "Github_Actions_Error_Analyzer"

# Generate output models
class Analyze_ErrorOutputAnalysis_Result(BaseModel):
    """Clear explanation of what caused the error"""
    root_cause: str
    error_category: str
    """Confidence in the root cause analysis"""
    confidence_level: str
    """Assessment of the impact on the development workflow"""
    impact_assessment: str
class Analyze_ErrorOutputRecommended_FixesItemCode_ChangesItem(BaseModel):
    file_path: Optional[str] = None
    suggested_change: Optional[str] = None
    change_type: Optional[str] = None
class Analyze_ErrorOutputRecommended_FixesItem(BaseModel):
    """Short title for the fix"""
    fix_title: str
    """Detailed description of the fix"""
    fix_description: str
    fix_type: str
    estimated_effort: str
    """Specific code changes needed"""
    code_changes: Optional[List[Analyze_ErrorOutputRecommended_FixesItemCode_ChangesItem]] = None
    """Commands to execute for the fix"""
    commands_to_run: Optional[List[str]] = None
    """Prerequisites for this fix"""
    prerequisites: Optional[List[str]] = None
class Analyze_ErrorOutputDeveloper_MessageRelated_DocumentationItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
class Analyze_ErrorOutputDeveloper_Message(BaseModel):
    """Brief summary for the developer"""
    summary: str
    """Detailed explanation in developer-friendly language"""
    detailed_explanation: str
    """Prioritized list of next steps"""
    next_steps: List[str]
    related_documentation: Optional[List[Analyze_ErrorOutputDeveloper_MessageRelated_DocumentationItem]] = None
    """Tips to prevent similar issues in the future"""
    prevention_tips: Optional[List[str]] = None
class Analyze_ErrorOutput(BaseModel):
    analysis_result: Analyze_ErrorOutputAnalysis_Result
    recommended_fixes: List[Analyze_ErrorOutputRecommended_FixesItem]
    developer_message: Analyze_ErrorOutputDeveloper_Message
    """How urgently this needs to be addressed"""
    urgency_level: str

class Generate_Pr_CommentOutputComment_Metadata(BaseModel):
    comment_type: str
    """Tags for categorizing the comment"""
    tags: List[str]
    urgency: str
class Generate_Pr_CommentOutput(BaseModel):
    """Formatted markdown comment for GitHub PR"""
    pr_comment: str
    comment_metadata: Generate_Pr_CommentOutputComment_Metadata

class Suggest_Workflow_ImprovementsOutputWorkflow_ImprovementsItem(BaseModel):
    improvement_title: str
    improvement_description: str
    improvement_type: str
    implementation_difficulty: str
    expected_benefit: str
    """Specific YAML changes needed"""
    workflow_changes: Optional[str] = None
class Suggest_Workflow_ImprovementsOutput(BaseModel):
    workflow_improvements: List[Suggest_Workflow_ImprovementsOutputWorkflow_ImprovementsItem]
    """General strategies to prevent similar issues"""
    prevention_strategies: List[str]
    """Recommendations for better monitoring"""
    monitoring_recommendations: List[str]


# Task functions

def parse_analyze_error_output(response) -> Analyze_ErrorOutput:
    """Parse LLM response into Analyze_ErrorOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Analyze_ErrorOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Analyze_ErrorOutput):
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
            "analysis_result": {
                "root_cause": "default_root_cause",
                "error_category": "default_error_category",
                "confidence_level": "default_confidence_level",
                "impact_assessment": "default_impact_assessment"
            },
            "recommended_fixes": [],
            "developer_message": {
                "summary": "default_summary",
                "detailed_explanation": "default_detailed_explanation",
                "next_steps": [],
                "related_documentation": [],
                "prevention_tips": []
            },
            "urgency_level": "how_default"
        }
        result = parse_with_fallback(
            response=response,
            model_class=Analyze_ErrorOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Analyze structured error data and provide developer-friendly explanations",
    role="analyst",
    behavioural_flags={"conservatism": "moderate", "verbosity": "comprehensive"},
    response_contract={"output_format": {"required_fields": ["analysis_result", "recommended_fixes", "developer_message", "urgency_level"]}}
)
def analyze_error(error_summary: Dict[str, Any], job_context: Dict[str, Any], log_statistics: Dict[str, Any], additional_context: Dict[str, Any], memory_summary: str = '') -> Analyze_ErrorOutput:
    """Process analyze_error task.

    Args:
        error_summary: {'type': 'object', 'properties': {'primary_error': {'type': 'string', 'description': 'The main error message extracted from logs'}, 'error_type': {'type': 'string', 'enum': ['build_failure', 'test_failure', 'dependency_error', 'syntax_error', 'runtime_error', 'timeout', 'permission_error', 'network_error', 'configuration_error', 'deployment_error', 'linting_error', 'other']}, 'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}, 'affected_files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of files mentioned in the error'}, 'stack_trace': {'type': 'string', 'description': 'Cleaned and formatted stack trace if available'}, 'error_context': {'type': 'string', 'description': 'Context around the error (before/after lines)'}, 'suggested_keywords': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Keywords for further analysis'}}, 'required': ['primary_error', 'error_type', 'severity']}
        job_context: {'type': 'object', 'properties': {'job_name': {'type': 'string'}, 'workflow_name': {'type': 'string'}, 'repository': {'type': 'string'}, 'branch': {'type': 'string'}, 'commit_sha': {'type': 'string'}, 'pr_number': {'type': 'integer'}, 'failed_step': {'type': 'string'}}, 'required': ['job_name', 'workflow_name', 'repository']}
        log_statistics: {'type': 'object', 'properties': {'total_lines': {'type': 'integer'}, 'error_lines': {'type': 'integer'}, 'warning_lines': {'type': 'integer'}, 'duration_estimate': {'type': 'string', 'description': 'Estimated job duration before failure'}}, 'required': ['total_lines', 'error_lines', 'warning_lines']}
        additional_context: {'type': 'object', 'properties': {'recent_changes': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Recent file changes or commits'}, 'build_commands': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Build commands that were executed'}, 'dependencies': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Dependencies mentioned in the build'}, 'environment_info': {'type': 'object', 'description': 'Environment information'}}}
        memory_summary: Optional memory context for the task

    Returns:
        Analyze_ErrorOutput
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
- analysis_result (required): object
  - root_cause (required): string
    Clear explanation of what caused the error
  - error_category (required): string
  - confidence_level (required): string
    Confidence in the root cause analysis
  - impact_assessment (required): string
    Assessment of the impact on the development workflow
- recommended_fixes (required): array of objects
  Each item contains:
    - fix_title (required): string
      Short title for the fix
    - fix_description (required): string
      Detailed description of the fix
    - fix_type (required): string
    - estimated_effort (required): string
    - code_changes (optional): array of objects
      Specific code changes needed
      Each item contains:
        - file_path (optional): string
        - suggested_change (optional): string
        - change_type (optional): string
    - commands_to_run (optional): array of strings
      Commands to execute for the fix
    - prerequisites (optional): array of strings
      Prerequisites for this fix
- developer_message (required): object
  - summary (required): string
    Brief summary for the developer
  - detailed_explanation (required): string
    Detailed explanation in developer-friendly language
  - next_steps (required): array of strings
    Prioritized list of next steps
  - related_documentation (optional): array of objects
    Each item contains:
      - title (optional): string
      - url (optional): string
  - prevention_tips (optional): array of strings
    Tips to prevent similar issues in the future
- urgency_level (required): string
  How urgently this needs to be addressed
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"analyze_error.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "error_summary": error_summary, "job_context": job_context, "log_statistics": log_statistics, "additional_context": additional_context
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
    "temperature": 0.3,
    "max_tokens": 2000
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_analyze_error_output(result)


def parse_generate_pr_comment_output(response) -> Generate_Pr_CommentOutput:
    """Parse LLM response into Generate_Pr_CommentOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Generate_Pr_CommentOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Generate_Pr_CommentOutput):
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
            "pr_comment": "formatted_default",
            "comment_metadata": {
                "comment_type": "default_comment_type",
                "tags": [],
                "urgency": "default_urgency"
            }
        }
        result = parse_with_fallback(
            response=response,
            model_class=Generate_Pr_CommentOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Generate a formatted comment for posting to a GitHub PR",
    role="analyst",
    behavioural_flags={"conservatism": "moderate", "verbosity": "comprehensive"},
    response_contract={"output_format": {"required_fields": ["pr_comment", "comment_metadata"]}}
)
def generate_pr_comment(analysis_result: Dict[str, Any], recommended_fixes: List[Any], developer_message: Dict[str, Any], pr_number: int, repository: str, job_name: str, workflow_name: str, memory_summary: str = '') -> Generate_Pr_CommentOutput:
    """Process generate_pr_comment task.

    Args:
        analysis_result: {'type': 'object', 'description': 'The analysis result from analyze_error task'}
        recommended_fixes: {'type': 'array', 'description': 'The recommended fixes from analyze_error task'}
        developer_message: {'type': 'object', 'description': 'The developer message from analyze_error task'}
        pr_number: {'type': 'integer', 'description': 'Pull request number'}
        repository: {'type': 'string', 'description': 'Repository name'}
        job_name: {'type': 'string', 'description': 'Failed job name'}
        workflow_name: {'type': 'string', 'description': 'Workflow name'}
        memory_summary: Optional memory context for the task

    Returns:
        Generate_Pr_CommentOutput
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
- pr_comment (required): string
  Formatted markdown comment for GitHub PR
- comment_metadata (required): object
  - comment_type (required): string
  - tags (required): array of strings
    Tags for categorizing the comment
  - urgency (required): string
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"generate_pr_comment.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "analysis_result": analysis_result, "recommended_fixes": recommended_fixes, "developer_message": developer_message, "pr_number": pr_number, "repository": repository, "job_name": job_name, "workflow_name": workflow_name
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
    "temperature": 0.3,
    "max_tokens": 2000
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_generate_pr_comment_output(result)


def parse_suggest_workflow_improvements_output(response) -> Suggest_Workflow_ImprovementsOutput:
    """Parse LLM response into Suggest_Workflow_ImprovementsOutput using DACP's enhanced parser.

    Args:
        response: Raw response from the LLM (str or dict)

    Returns:
        Parsed and validated Suggest_Workflow_ImprovementsOutput instance

    Raises:
        ValueError: If the response cannot be parsed
    """
    if isinstance(response, Suggest_Workflow_ImprovementsOutput):
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
            "workflow_improvements": [],
            "prevention_strategies": [],
            "monitoring_recommendations": []
        }
        result = parse_with_fallback(
            response=response,
            model_class=Suggest_Workflow_ImprovementsOutput,
            **defaults
        )
        return result
    except Exception as e:
        raise ValueError(f'Error parsing response with DACP parser: {e}')


@behavioural_contract(
    version="0.1.2",
    description="Suggest improvements to the GitHub Actions workflow to prevent similar issues",
    role="analyst",
    behavioural_flags={"conservatism": "moderate", "verbosity": "comprehensive"},
    response_contract={"output_format": {"required_fields": ["workflow_improvements", "prevention_strategies", "monitoring_recommendations"]}}
)
def suggest_workflow_improvements(error_analysis: Dict[str, Any], workflow_name: str, repository: str, recurring_patterns: List[Any], memory_summary: str = '') -> Suggest_Workflow_ImprovementsOutput:
    """Process suggest_workflow_improvements task.

    Args:
        error_analysis: {'type': 'object', 'description': 'Previous analysis result'}
        workflow_name: {'type': 'string', 'description': 'Name of the workflow'}
        repository: {'type': 'string', 'description': 'Repository name'}
        recurring_patterns: {'type': 'array', 'items': {'type': 'string'}, 'description': 'Patterns of recurring issues'}
        memory_summary: Optional memory context for the task

    Returns:
        Suggest_Workflow_ImprovementsOutput
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
- workflow_improvements (required): array of objects
  Each item contains:
    - improvement_title (required): string
    - improvement_description (required): string
    - improvement_type (required): string
    - implementation_difficulty (required): string
    - expected_benefit (required): string
    - workflow_changes (optional): string
      Specific YAML changes needed
- prevention_strategies (required): array of strings
  General strategies to prevent similar issues
- monitoring_recommendations (required): array of strings
  Recommendations for better monitoring
"""

    # Load and render the prompt template
    prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
    env = Environment(loader=FileSystemLoader([".", prompts_dir]))
    try:
        template = env.get_template(f"suggest_workflow_improvements.jinja2")
    except FileNotFoundError:
        log.warning(f"Task-specific prompt template not found, using default template")
        template = env.get_template("agent_prompt.jinja2")

    # Create input dictionary for template
    input_dict = {
        "error_analysis": error_analysis, "workflow_name": workflow_name, "repository": repository, "recurring_patterns": recurring_patterns
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
    "temperature": 0.3,
    "max_tokens": 2000
}

    # Call the LLM using DACP
    result = invoke_intelligence(prompt, intelligence_config)
    return parse_suggest_workflow_improvements_output(result)



class GithubActionsErrorAnalyzerAgent(dacp.Agent):
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
                "log_file": "./logs/github-actions-analyzer.log",
                "env_overrides": {
                    "level": "DACP_LOG_LEVEL",
                    "format_style": "DACP_LOG_STYLE",
                    "log_file": "DACP_LOG_FILE_ANALYZER"
                }
            },
            "intelligence": {
                "engine": "openai",
                "model": "gpt-4",
                "endpoint": "https://api.openai.com/v1",
                "config": {
                    "temperature": 0.3,
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



    def analyze_error(self, error_summary, job_context, log_statistics, additional_context) -> Analyze_ErrorOutput:
        """Process analyze_error task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return analyze_error(error_summary, job_context, log_statistics, additional_context, memory_summary=memory_summary)


    def generate_pr_comment(self, analysis_result, recommended_fixes, developer_message, pr_number, repository, job_name, workflow_name) -> Generate_Pr_CommentOutput:
        """Process generate_pr_comment task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return generate_pr_comment(analysis_result, recommended_fixes, developer_message, pr_number, repository, job_name, workflow_name, memory_summary=memory_summary)


    def suggest_workflow_improvements(self, error_analysis, workflow_name, repository, recurring_patterns) -> Suggest_Workflow_ImprovementsOutput:
        """Process suggest_workflow_improvements task."""
        memory_summary = self.get_memory() if hasattr(self, 'get_memory') else ""
        return suggest_workflow_improvements(error_analysis, workflow_name, repository, recurring_patterns, memory_summary=memory_summary)



def main():
    # Example usage - in production, you would get these from your orchestrator setup
    from dacp.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    agent = GithubActionsErrorAnalyzerAgent("example-agent-id", orchestrator)

    # Example usage with analyze_error task: analyze_error
    result = agent.analyze_error(error_summary="example_error_summary", job_context="example_job_context", log_statistics="example_log_statistics", additional_context="example_additional_context")
    # Handle both Pydantic models and dictionaries
    if hasattr(result, 'model_dump'):
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()