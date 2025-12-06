"""
Unit tests for SkylarIQ agent
"""

import pytest
import asyncio
from src.agent import create_agent
from src.state import InputPayload


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent can be initialized"""
    agent = await create_agent()
    assert agent is not None
    await agent.close()


@pytest.mark.asyncio
async def test_process_simple_request():
    """Test processing a simple customer request"""
    agent = await create_agent()

    request = InputPayload(
        customer_name="Test User",
        email="test@example.com",
        query="I need help with my account",
        priority="medium",
        ticket_id="TEST-001"
    )

    output = await agent.process_request(request)

    # Verify output structure
    assert output.ticket_id == "TEST-001"
    assert output.customer_name == "Test User"
    assert output.status is not None
    assert output.response is not None
    assert isinstance(output.escalated, bool)
    assert len(output.execution_logs) == 11  # All 11 stages

    await agent.close()


@pytest.mark.asyncio
async def test_high_priority_request():
    """Test high priority request handling"""
    agent = await create_agent()

    request = InputPayload(
        customer_name="VIP Customer",
        email="vip@enterprise.com",
        query="Critical system failure affecting production",
        priority="critical",
        ticket_id="TEST-002"
    )

    output = await agent.process_request(request)

    assert output.priority == "critical"
    assert output.solution_confidence is not None

    await agent.close()


@pytest.mark.asyncio
async def test_multiple_requests():
    """Test processing multiple requests sequentially"""
    agent = await create_agent()

    requests = [
        InputPayload(
            customer_name=f"User {i}",
            email=f"user{i}@example.com",
            query=f"Query {i}",
            priority="medium",
            ticket_id=f"TEST-{i:03d}"
        )
        for i in range(1, 4)
    ]

    outputs = []
    for request in requests:
        output = await agent.process_request(request)
        outputs.append(output)

    assert len(outputs) == 3
    assert all(o.ticket_id.startswith("TEST-") for o in outputs)

    await agent.close()


@pytest.mark.asyncio
async def test_state_persistence():
    """Test that state is maintained across stages"""
    agent = await create_agent()

    request = InputPayload(
        customer_name="State Test",
        email="state@example.com",
        query="Testing state persistence",
        priority="low",
        ticket_id="TEST-STATE-001"
    )

    output = await agent.process_request(request)

    # Check that all stages were executed
    stage_names = [log["stage"] for log in output.execution_logs]
    expected_stages = [
        "INTAKE", "UNDERSTAND", "PREPARE", "ASK",
        "RETRIEVE", "DECIDE", "UPDATE", "CREATE", "DO", "COMPLETE"
    ]

    for expected in expected_stages:
        assert expected in stage_names

    await agent.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
