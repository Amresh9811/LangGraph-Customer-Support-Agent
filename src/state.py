"""
State management for the LangGraph agent.
Defines the state schema that persists across all stages.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class CustomerSupportState(TypedDict):
    """
    State schema for customer support workflow.
    This state is passed between all stages and persists data.
    """
    # Input fields
    customer_name: str
    email: str
    query: str
    priority: str  # low, medium, high, critical
    ticket_id: str

    # UNDERSTAND stage outputs
    parsed_query: Optional[Dict[str, Any]]
    extracted_entities: Optional[Dict[str, Any]]

    # PREPARE stage outputs
    normalized_data: Optional[Dict[str, Any]]
    enrichment_flags: Optional[Dict[str, Any]]

    # ASK stage outputs
    clarification_needed: bool
    clarification_questions: Optional[List[str]]

    # WAIT stage outputs
    clarification_answers: Optional[Dict[str, str]]

    # RETRIEVE stage outputs
    knowledge_results: Optional[List[Dict[str, Any]]]

    # DECIDE stage outputs
    solution_score: Optional[float]
    escalation_required: bool
    selected_solution: Optional[Dict[str, Any]]

    # UPDATE stage outputs
    ticket_status: Optional[str]

    # CREATE stage outputs
    generated_response: Optional[str]

    # DO stage outputs
    api_results: Optional[Dict[str, Any]]
    notification_status: Optional[str]

    # COMPLETE stage outputs
    final_output: Optional[Dict[str, Any]]

    # Metadata
    stage_logs: List[Dict[str, Any]]
    current_stage: Optional[str]


class InputPayload(BaseModel):
    """Input payload schema for customer support requests"""
    customer_name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email address")
    query: str = Field(..., description="Customer query or issue description")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    ticket_id: str = Field(..., description="Unique ticket identifier")


class OutputPayload(BaseModel):
    """Final output payload after workflow completion"""
    ticket_id: str
    customer_name: str
    email: str
    original_query: str
    priority: str
    status: str
    response: str
    solution_confidence: Optional[float] = None
    escalated: bool = False
    execution_logs: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


def create_initial_state(input_payload: InputPayload) -> CustomerSupportState:
    """
    Create initial state from input payload.

    Args:
        input_payload: Input customer support request

    Returns:
        Initial CustomerSupportState
    """
    return CustomerSupportState(
        customer_name=input_payload.customer_name,
        email=input_payload.email,
        query=input_payload.query,
        priority=input_payload.priority,
        ticket_id=input_payload.ticket_id,
        parsed_query=None,
        extracted_entities=None,
        normalized_data=None,
        enrichment_flags=None,
        clarification_needed=False,
        clarification_questions=None,
        clarification_answers=None,
        knowledge_results=None,
        solution_score=None,
        escalation_required=False,
        selected_solution=None,
        ticket_status=None,
        generated_response=None,
        api_results=None,
        notification_status=None,
        final_output=None,
        stage_logs=[],
        current_stage=None
    )


def log_stage_execution(state: CustomerSupportState, stage_name: str,
                        abilities: List[str], server: str,
                        outputs: Dict[str, Any]) -> CustomerSupportState:
    """
    Log stage execution details to state.

    Args:
        state: Current state
        stage_name: Name of the stage
        abilities: List of abilities executed
        server: MCP server used (atlas/common)
        outputs: Stage execution outputs

    Returns:
        Updated state with log entry
    """
    log_entry = {
        "stage": stage_name,
        "abilities": abilities,
        "server": server,
        "outputs": outputs,
        "timestamp": None  # Will be set during execution
    }
    state["stage_logs"].append(log_entry)
    state["current_stage"] = stage_name
    return state
