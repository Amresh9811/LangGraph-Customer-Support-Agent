"""
Unit tests for state management
"""

import pytest
from src.state import InputPayload, OutputPayload, create_initial_state


def test_input_payload_creation():
    """Test InputPayload creation and validation"""
    payload = InputPayload(
        customer_name="John Doe",
        email="john@example.com",
        query="Test query",
        priority="high",
        ticket_id="TEST-001"
    )

    assert payload.customer_name == "John Doe"
    assert payload.email == "john@example.com"
    assert payload.priority == "high"


def test_input_payload_defaults():
    """Test InputPayload default values"""
    payload = InputPayload(
        customer_name="Jane Doe",
        email="jane@example.com",
        query="Test query",
        ticket_id="TEST-002"
    )

    assert payload.priority == "medium"  # Default


def test_create_initial_state():
    """Test initial state creation"""
    payload = InputPayload(
        customer_name="Test User",
        email="test@example.com",
        query="Test query",
        priority="low",
        ticket_id="TEST-003"
    )

    state = create_initial_state(payload)

    # Check input fields are copied
    assert state["customer_name"] == "Test User"
    assert state["email"] == "test@example.com"
    assert state["query"] == "Test query"
    assert state["priority"] == "low"
    assert state["ticket_id"] == "TEST-003"

    # Check defaults
    assert state["parsed_query"] is None
    assert state["extracted_entities"] is None
    assert state["clarification_needed"] is False
    assert state["escalation_required"] is False
    assert state["stage_logs"] == []


def test_output_payload_structure():
    """Test OutputPayload structure"""
    output = OutputPayload(
        ticket_id="TEST-004",
        customer_name="Test Customer",
        email="customer@example.com",
        original_query="Original query",
        priority="medium",
        status="resolved",
        response="Response message",
        solution_confidence=0.95,
        escalated=False,
        execution_logs=[],
        metadata={"test": "data"}
    )

    assert output.ticket_id == "TEST-004"
    assert output.status == "resolved"
    assert output.solution_confidence == 0.95
    assert output.escalated is False
    assert output.metadata["test"] == "data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
