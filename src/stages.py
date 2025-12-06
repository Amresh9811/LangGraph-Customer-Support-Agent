"""
Stage implementations for the customer support workflow.
Each stage is a node in the LangGraph that processes and updates state.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .state import CustomerSupportState, log_stage_execution
from .mcp_client import MCPClient


logger = logging.getLogger(__name__)


class StageExecutor:
    """Base class for stage execution"""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    def _log_execution(self, state: CustomerSupportState, stage_name: str,
                      abilities: list, server: str, outputs: Dict[str, Any]) -> CustomerSupportState:
        """Add execution log with timestamp (stores only essential data to avoid recursion)"""
        # Only store success status and ability names, not full nested results
        log_entry = {
            "stage": stage_name,
            "abilities": abilities,
            "server": server,
            "success": outputs.get("success", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        state["stage_logs"].append(log_entry)
        state["current_stage"] = stage_name
        return state


class IntakeStage(StageExecutor):
    """📥 INTAKE: Accept and validate incoming payload"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute INTAKE stage"""
        logger.info("📥 Executing INTAKE stage")

        abilities = ["accept_payload"]
        context = {
            "customer_name": state["customer_name"],
            "email": state["email"],
            "query": state["query"],
            "priority": state["priority"],
            "ticket_id": state["ticket_id"]
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        state = self._log_execution(state, "INTAKE", abilities, "common", result)
        logger.info("✓ INTAKE stage completed")

        return state


class UnderstandStage(StageExecutor):
    """🧠 UNDERSTAND: Parse and extract entities from request"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute UNDERSTAND stage"""
        logger.info("🧠 Executing UNDERSTAND stage")

        abilities = ["parse_request_text", "extract_entities"]
        context = {
            "customer_name": state["customer_name"],
            "query": state["query"],
            "email": state["email"],
            "priority": state["priority"]
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "parse_request_text" in results:
                state["parsed_query"] = results["parse_request_text"]["data"].get("parsed_query")
            if "extract_entities" in results:
                state["extracted_entities"] = results["extract_entities"]["data"].get("extracted_entities")

        state = self._log_execution(state, "UNDERSTAND", abilities, "common", result)
        logger.info("✓ UNDERSTAND stage completed")

        return state


class PrepareStage(StageExecutor):
    """🛠️ PREPARE: Normalize and enrich data"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute PREPARE stage"""
        logger.info("🛠️ Executing PREPARE stage")

        abilities = ["normalize_fields", "enrich_records", "add_flags_calculations"]
        context = {
            "customer_name": state["customer_name"],
            "email": state["email"],
            "query": state["query"],
            "priority": state["priority"],
            "extracted_entities": state.get("extracted_entities")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "normalize_fields" in results:
                state["normalized_data"] = results["normalize_fields"]["data"].get("normalized_data")
            if "enrich_records" in results:
                enrichment = results["enrich_records"]["data"].get("enrichment_data", {})
                if not state.get("normalized_data"):
                    state["normalized_data"] = {}
                state["normalized_data"]["enrichment"] = enrichment
            if "add_flags_calculations" in results:
                state["enrichment_flags"] = results["add_flags_calculations"]["data"].get("enrichment_flags")

        state = self._log_execution(state, "PREPARE", abilities, "common", result)
        logger.info("✓ PREPARE stage completed")

        return state


class AskStage(StageExecutor):
    """❓ ASK: Request clarification if needed"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute ASK stage"""
        logger.info("❓ Executing ASK stage")

        abilities = ["clarify_question"]
        context = {
            "query": state["query"],
            "priority": state["priority"],
            "parsed_query": state.get("parsed_query")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "clarify_question" in results:
                data = results["clarify_question"]["data"]
                state["clarification_needed"] = data.get("clarification_needed", False)
                state["clarification_questions"] = data.get("clarification_questions", [])

        state = self._log_execution(state, "ASK", abilities, "common", result)
        logger.info(f"✓ ASK stage completed - Clarification needed: {state['clarification_needed']}")

        return state


class WaitStage(StageExecutor):
    """⏳ WAIT: Extract and store answers"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute WAIT stage"""
        logger.info("⏳ Executing WAIT stage")

        # Skip if no clarification needed
        if not state.get("clarification_needed"):
            logger.info("✓ WAIT stage skipped - no clarification needed")
            return state

        abilities = ["extract_answer", "store_answer"]
        context = {
            "clarification_questions": state.get("clarification_questions", [])
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "store_answer" in results:
                state["clarification_answers"] = results["store_answer"]["data"].get("clarification_answers")

        state = self._log_execution(state, "WAIT", abilities, "common", result)
        logger.info("✓ WAIT stage completed")

        return state


class RetrieveStage(StageExecutor):
    """📚 RETRIEVE: Search knowledge base"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute RETRIEVE stage"""
        logger.info("📚 Executing RETRIEVE stage")

        abilities = ["knowledge_base_search", "store_data"]
        context = {
            "query": state["query"],
            "parsed_query": state.get("parsed_query"),
            "extracted_entities": state.get("extracted_entities"),
            "clarification_answers": state.get("clarification_answers")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "store_data" in results:
                state["knowledge_results"] = results["store_data"]["data"].get("knowledge_results")

        state = self._log_execution(state, "RETRIEVE", abilities, "atlas", result)
        logger.info(f"✓ RETRIEVE stage completed - Found {len(state.get('knowledge_results', []))} results")

        return state


class DecideStage(StageExecutor):
    """⚖️ DECIDE: Evaluate solutions and decide on escalation (Non-deterministic)"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute DECIDE stage with non-deterministic orchestration"""
        logger.info("⚖️ Executing DECIDE stage (non-deterministic)")

        # First, evaluate solution
        eval_result = await self.mcp_client.execute_ability(
            "solution_evaluation",
            {
                "knowledge_results": state.get("knowledge_results", [])
            }
        )

        if eval_result.get("success"):
            data = eval_result["data"]
            state["solution_score"] = data.get("solution_score", 0.0)
            state["selected_solution"] = data.get("selected_solution")

        # Dynamic decision: Check if escalation is needed based on score
        escalation_result = await self.mcp_client.execute_ability(
            "escalation_decision",
            {
                "solution_score": state["solution_score"],
                "priority": state["priority"]
            }
        )

        if escalation_result.get("success"):
            state["escalation_required"] = escalation_result["data"].get("escalation_required", False)

        # Update payload based on decision
        update_result = await self.mcp_client.execute_ability(
            "update_payload",
            {
                "solution_score": state["solution_score"],
                "escalation_required": state["escalation_required"],
                "selected_solution": state["selected_solution"]
            }
        )

        # Combine results
        abilities = ["solution_evaluation", "escalation_decision", "update_payload"]
        combined_result = {
            "success": all([
                eval_result.get("success"),
                escalation_result.get("success"),
                update_result.get("success")
            ]),
            "results": {
                "solution_evaluation": eval_result,
                "escalation_decision": escalation_result,
                "update_payload": update_result
            }
        }

        state = self._log_execution(state, "DECIDE", abilities, "common", combined_result)
        logger.info(f"✓ DECIDE stage completed - Score: {state['solution_score']:.2f}, "
                   f"Escalate: {state['escalation_required']}")

        return state


class UpdateStage(StageExecutor):
    """🔄 UPDATE: Update ticket in external system"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute UPDATE stage"""
        logger.info("🔄 Executing UPDATE stage")

        # Choose abilities based on escalation status
        if state.get("escalation_required"):
            abilities = ["update_ticket"]  # Only update, don't close if escalated
        else:
            abilities = ["update_ticket", "close_ticket"]

        context = {
            "ticket_id": state["ticket_id"],
            "escalation_required": state.get("escalation_required"),
            "solution_score": state.get("solution_score")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            # Get status from the last ability executed
            last_ability = abilities[-1]
            if last_ability in results:
                state["ticket_status"] = results[last_ability]["data"].get("ticket_status")

        state = self._log_execution(state, "UPDATE", abilities, "atlas", result)
        logger.info(f"✓ UPDATE stage completed - Status: {state.get('ticket_status')}")

        return state


class CreateStage(StageExecutor):
    """✍️ CREATE: Generate customer response"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute CREATE stage"""
        logger.info("✍️ Executing CREATE stage")

        abilities = ["response_generation"]
        context = {
            "customer_name": state["customer_name"],
            "ticket_id": state["ticket_id"],
            "selected_solution": state.get("selected_solution"),
            "escalation_required": state.get("escalation_required")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "response_generation" in results:
                state["generated_response"] = results["response_generation"]["data"].get("generated_response")

        state = self._log_execution(state, "CREATE", abilities, "common", result)
        logger.info("✓ CREATE stage completed")

        return state


class DoStage(StageExecutor):
    """🏃 DO: Execute external actions"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute DO stage"""
        logger.info("🏃 Executing DO stage")

        abilities = ["execute_api_calls", "trigger_notifications"]
        context = {
            "ticket_id": state["ticket_id"],
            "customer_email": state["email"],
            "generated_response": state.get("generated_response"),
            "escalation_required": state.get("escalation_required")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "execute_api_calls" in results:
                state["api_results"] = results["execute_api_calls"]["data"].get("api_results")
            if "trigger_notifications" in results:
                state["notification_status"] = results["trigger_notifications"]["data"].get("notification_status")

        state = self._log_execution(state, "DO", abilities, "atlas", result)
        logger.info("✓ DO stage completed")

        return state


class CompleteStage(StageExecutor):
    """✅ COMPLETE: Output final structured payload"""

    async def execute(self, state: CustomerSupportState) -> CustomerSupportState:
        """Execute COMPLETE stage"""
        logger.info("✅ Executing COMPLETE stage")

        abilities = ["output_payload"]
        context = {
            "ticket_id": state["ticket_id"],
            "customer_name": state["customer_name"],
            "email": state["email"],
            "query": state["query"],
            "priority": state["priority"],
            "ticket_status": state.get("ticket_status"),
            "generated_response": state.get("generated_response"),
            "escalation_required": state.get("escalation_required"),
            "solution_score": state.get("solution_score")
        }

        result = await self.mcp_client.execute_abilities(abilities, context)

        # Extract results
        if result.get("success"):
            results = result["results"]
            if "output_payload" in results:
                state["final_output"] = results["output_payload"]["data"].get("final_output")

        state = self._log_execution(state, "COMPLETE", abilities, "common", result)
        logger.info("✅ COMPLETE stage completed")

        return state
