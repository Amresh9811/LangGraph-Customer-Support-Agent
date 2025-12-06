"""
SkylarIQ - LangGraph Customer Support Agent
Main agent orchestrator using LangGraph's StateGraph
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import CustomerSupportState, InputPayload, OutputPayload, create_initial_state
from .mcp_client import MCPClient
from .stages import (
    IntakeStage, UnderstandStage, PrepareStage, AskStage, WaitStage,
    RetrieveStage, DecideStage, UpdateStage, CreateStage, DoStage, CompleteStage
)


logger = logging.getLogger(__name__)


class SkylarIQAgent:
    """
    SkylarIQ - Customer Support Agent using LangGraph.

    This agent orchestrates a 11-stage customer support workflow:
    INTAKE → UNDERSTAND → PREPARE → ASK → WAIT → RETRIEVE → DECIDE → UPDATE → CREATE → DO → COMPLETE

    Features:
    - State persistence across all stages
    - Deterministic and non-deterministic stage execution
    - MCP client integration for Atlas and Common servers
    - Comprehensive logging and tracing
    """

    def __init__(self, atlas_url: str, common_url: str):
        """
        Initialize SkylarIQ agent.

        Args:
            atlas_url: URL for Atlas MCP server
            common_url: URL for Common MCP server
        """
        self.mcp_client = MCPClient(atlas_url, common_url)

        # Initialize stages
        self.intake = IntakeStage(self.mcp_client)
        self.understand = UnderstandStage(self.mcp_client)
        self.prepare = PrepareStage(self.mcp_client)
        self.ask = AskStage(self.mcp_client)
        self.wait = WaitStage(self.mcp_client)
        self.retrieve = RetrieveStage(self.mcp_client)
        self.decide = DecideStage(self.mcp_client)
        self.update = UpdateStage(self.mcp_client)
        self.create = CreateStage(self.mcp_client)
        self.do = DoStage(self.mcp_client)
        self.complete = CompleteStage(self.mcp_client)

        # Build workflow graph
        self.workflow = self._build_workflow()

        logger.info("SkylarIQ Agent initialized successfully")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with all 11 stages.

        Returns:
            Compiled StateGraph workflow
        """
        # Create state graph
        workflow = StateGraph(CustomerSupportState)

        # Add nodes (stages)
        workflow.add_node("intake", self.intake.execute)
        workflow.add_node("understand", self.understand.execute)
        workflow.add_node("prepare", self.prepare.execute)
        workflow.add_node("ask", self.ask.execute)
        workflow.add_node("wait", self.wait.execute)
        workflow.add_node("retrieve", self.retrieve.execute)
        workflow.add_node("decide", self.decide.execute)
        workflow.add_node("update", self.update.execute)
        workflow.add_node("create", self.create.execute)
        workflow.add_node("do", self.do.execute)
        workflow.add_node("complete", self.complete.execute)

        # Set entry point
        workflow.set_entry_point("intake")

        # Add deterministic edges (sequential flow)
        workflow.add_edge("intake", "understand")
        workflow.add_edge("understand", "prepare")
        workflow.add_edge("prepare", "ask")

        # Conditional edge: ASK → WAIT (if clarification needed) or RETRIEVE (skip)
        workflow.add_conditional_edges(
            "ask",
            self._should_wait_for_clarification,
            {
                "wait": "wait",
                "retrieve": "retrieve"
            }
        )

        workflow.add_edge("wait", "retrieve")
        workflow.add_edge("retrieve", "decide")
        workflow.add_edge("decide", "update")
        workflow.add_edge("update", "create")
        workflow.add_edge("create", "do")
        workflow.add_edge("do", "complete")

        # End workflow
        workflow.add_edge("complete", END)

        # Compile with memory checkpointer for state persistence
        memory = MemorySaver()
        compiled_workflow = workflow.compile(checkpointer=memory)

        logger.info("Workflow graph compiled successfully")
        return compiled_workflow

    def _should_wait_for_clarification(self, state: CustomerSupportState) -> str:
        """
        Conditional routing: Determine if WAIT stage is needed.

        Args:
            state: Current state

        Returns:
            Next stage name ("wait" or "retrieve")
        """
        if state.get("clarification_needed"):
            return "wait"
        return "retrieve"

    async def process_request(self, input_payload: InputPayload) -> OutputPayload:
        """
        Process a customer support request through the entire workflow.

        Args:
            input_payload: Customer support request

        Returns:
            Final output payload with results
        """
        logger.info(f"Processing ticket: {input_payload.ticket_id}")
        logger.info(f"Customer: {input_payload.customer_name} ({input_payload.email})")
        logger.info(f"Priority: {input_payload.priority}")
        logger.info(f"Query: {input_payload.query}")

        # Create initial state
        initial_state = create_initial_state(input_payload)

        # Execute workflow
        config = {"configurable": {"thread_id": input_payload.ticket_id}}
        final_state = await self.workflow.ainvoke(initial_state, config)

        # Build output payload
        output = self._build_output_payload(input_payload, final_state)

        logger.info(f"Ticket {input_payload.ticket_id} processing completed")
        logger.info(f"Status: {output.status}")
        logger.info(f"Escalated: {output.escalated}")

        return output

    def _build_output_payload(self, input_payload: InputPayload,
                             final_state: CustomerSupportState) -> OutputPayload:
        """
        Build final output payload from state.

        Args:
            input_payload: Original input
            final_state: Final workflow state

        Returns:
            Structured output payload
        """
        return OutputPayload(
            ticket_id=input_payload.ticket_id,
            customer_name=input_payload.customer_name,
            email=input_payload.email,
            original_query=input_payload.query,
            priority=input_payload.priority,
            status=final_state.get("ticket_status", "processed"),
            response=final_state.get("generated_response", ""),
            solution_confidence=final_state.get("solution_score"),
            escalated=final_state.get("escalation_required", False),
            execution_logs=final_state.get("stage_logs", []),
            metadata={
                "parsed_query": final_state.get("parsed_query"),
                "extracted_entities": final_state.get("extracted_entities"),
                "knowledge_results_count": len(final_state.get("knowledge_results", [])),
                "clarification_needed": final_state.get("clarification_needed", False),
                "notification_status": final_state.get("notification_status")
            }
        )

    async def close(self):
        """Cleanup resources"""
        await self.mcp_client.close()
        logger.info("SkylarIQ Agent closed")


async def create_agent(atlas_url: str = "http://localhost:8001",
                       common_url: str = "http://localhost:8002") -> SkylarIQAgent:
    """
    Factory function to create SkylarIQ agent.

    Args:
        atlas_url: Atlas MCP server URL
        common_url: Common MCP server URL

    Returns:
        Initialized SkylarIQ agent
    """
    return SkylarIQAgent(atlas_url, common_url)
