"""
MCP (Model Context Protocol) Client Integration.
Handles communication with Atlas and Common MCP servers.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import httpx
import asyncio


logger = logging.getLogger(__name__)


class MCPServer(Enum):
    """MCP Server types"""
    ATLAS = "atlas"
    COMMON = "common"


class MCPClient:
    """
    Client for interacting with MCP servers.
    Routes ability execution to appropriate server (Atlas or Common).
    """

    def __init__(self, atlas_url: str, common_url: str):
        """
        Initialize MCP client.

        Args:
            atlas_url: URL for Atlas MCP server (external abilities)
            common_url: URL for Common MCP server (internal abilities)
        """
        self.atlas_url = atlas_url
        self.common_url = common_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Map abilities to servers
        self.server_mapping = {
            # Common server abilities (no external dependencies)
            "accept_payload": MCPServer.COMMON,
            "parse_request_text": MCPServer.COMMON,
            "extract_entities": MCPServer.COMMON,
            "normalize_fields": MCPServer.COMMON,
            "enrich_records": MCPServer.COMMON,
            "add_flags_calculations": MCPServer.COMMON,
            "clarify_question": MCPServer.COMMON,
            "extract_answer": MCPServer.COMMON,
            "store_answer": MCPServer.COMMON,
            "store_data": MCPServer.COMMON,
            "solution_evaluation": MCPServer.COMMON,
            "escalation_decision": MCPServer.COMMON,
            "update_payload": MCPServer.COMMON,
            "response_generation": MCPServer.COMMON,
            "output_payload": MCPServer.COMMON,

            # Atlas server abilities (external system interaction)
            "knowledge_base_search": MCPServer.ATLAS,
            "update_ticket": MCPServer.ATLAS,
            "close_ticket": MCPServer.ATLAS,
            "execute_api_calls": MCPServer.ATLAS,
            "trigger_notifications": MCPServer.ATLAS,
        }

    def get_server_url(self, server: MCPServer) -> str:
        """Get URL for specified server"""
        return self.atlas_url if server == MCPServer.ATLAS else self.common_url

    async def execute_ability(self, ability_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single ability via appropriate MCP server.

        Args:
            ability_name: Name of the ability to execute
            context: Context data for ability execution

        Returns:
            Ability execution result
        """
        server = self.server_mapping.get(ability_name)
        if not server:
            logger.warning(f"Unknown ability: {ability_name}, defaulting to COMMON server")
            server = MCPServer.COMMON

        server_url = self.get_server_url(server)

        logger.info(f"Executing ability '{ability_name}' via {server.value} server at {server_url}")

        try:
            # Simulate MCP ability execution
            # In production, this would make actual HTTP calls to MCP servers
            result = await self._simulate_ability_execution(ability_name, context, server)
            logger.info(f"Successfully executed {ability_name}")
            return result

        except Exception as e:
            logger.error(f"Error executing ability {ability_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ability": ability_name
            }

    async def execute_abilities(self, ability_names: List[str],
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multiple abilities in sequence.

        Args:
            ability_names: List of abilities to execute
            context: Context data for execution

        Returns:
            Combined execution results
        """
        results = {}
        current_context = context.copy()

        for ability_name in ability_names:
            result = await self.execute_ability(ability_name, current_context)
            results[ability_name] = result

            # Update context with results for next ability
            if result.get("success"):
                current_context.update(result.get("data", {}))

        # Don't return updated_context to avoid deep nesting in state logs
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "results": results
        }

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine intent, category, and keywords"""
        query_lower = query.lower()

        # Determine intent and category based on keywords
        if any(word in query_lower for word in ['refund', 'return', 'money back', 'charge', 'charged', 'billing', 'payment']):
            return {
                "intent": "refund_request",
                "category": "billing",
                "keywords": ["refund", "payment", "billing"],
                "issue_type": "billing"
            }
        elif any(word in query_lower for word in ['password', 'login', 'log in', 'sign in', 'access', 'locked', 'forgot']):
            return {
                "intent": "technical_support",
                "category": "account_access",
                "keywords": ["password", "reset", "login"],
                "issue_type": "authentication"
            }
        elif any(word in query_lower for word in ['api', '403', '500', 'forbidden', 'error code', 'endpoint', 'integration']):
            return {
                "intent": "technical_support",
                "category": "api_integration",
                "keywords": ["api", "integration", "error"],
                "issue_type": "api"
            }
        elif any(word in query_lower for word in ['crash', 'error', 'bug', 'not working', 'broken', 'issue', 'problem']):
            return {
                "intent": "technical_support",
                "category": "technical_issue",
                "keywords": ["error", "bug", "technical"],
                "issue_type": "technical"
            }
        elif any(word in query_lower for word in ['food', 'quality', 'product', 'defect', 'damaged', 'poor']):
            return {
                "intent": "product_complaint",
                "category": "product_quality",
                "keywords": ["quality", "product", "complaint"],
                "issue_type": "product_quality"
            }
        elif any(word in query_lower for word in ['feature', 'request', 'add', 'would like', 'suggestion']):
            return {
                "intent": "feature_request",
                "category": "enhancement",
                "keywords": ["feature", "request", "enhancement"],
                "issue_type": "feature_request"
            }
        elif any(word in query_lower for word in ['account', 'username', 'email', 'profile', 'settings']):
            return {
                "intent": "account_management",
                "category": "account_settings",
                "keywords": ["account", "settings", "profile"],
                "issue_type": "account"
            }
        else:
            return {
                "intent": "general_inquiry",
                "category": "general",
                "keywords": ["support", "help"],
                "issue_type": "general"
            }

    async def _simulate_ability_execution(self, ability_name: str,
                                          context: Dict[str, Any],
                                          server: MCPServer) -> Dict[str, Any]:
        """
        Simulate ability execution.
        In production, replace with actual MCP server calls.

        Args:
            ability_name: Ability to execute
            context: Execution context
            server: Server type

        Returns:
            Simulated execution result
        """
        # Simulate network delay
        await asyncio.sleep(0.1)

        # Ability-specific simulation logic
        if ability_name == "accept_payload":
            return {
                "success": True,
                "data": {
                    "validated": True,
                    "payload": context
                },
                "server": server.value
            }

        elif ability_name == "parse_request_text":
            # Analyze the query dynamically
            query = context.get("query", "")
            analysis = self._analyze_query(query)

            return {
                "success": True,
                "data": {
                    "parsed_query": {
                        "intent": analysis["intent"],
                        "category": analysis["category"],
                        "urgency": context.get("priority", "medium"),
                        "keywords": analysis["keywords"]
                    }
                },
                "server": server.value
            }

        elif ability_name == "extract_entities":
            # Extract entities based on query analysis
            query = context.get("query", "")
            analysis = self._analyze_query(query)

            return {
                "success": True,
                "data": {
                    "extracted_entities": {
                        "customer_name": context.get("customer_name"),
                        "email": context.get("email"),
                        "issue_type": analysis["issue_type"],
                        "product": "web_portal"
                    }
                },
                "server": server.value
            }

        elif ability_name == "normalize_fields":
            return {
                "success": True,
                "data": {
                    "normalized_data": {
                        "email": context.get("email", "").lower().strip(),
                        "priority": context.get("priority", "medium").lower(),
                        "query": context.get("query", "").strip()
                    }
                },
                "server": server.value
            }

        elif ability_name == "enrich_records":
            return {
                "success": True,
                "data": {
                    "enrichment_data": {
                        "customer_tier": "premium",
                        "account_age_days": 365,
                        "previous_tickets": 2,
                        "satisfaction_score": 4.5
                    }
                },
                "server": server.value
            }

        elif ability_name == "add_flags_calculations":
            return {
                "success": True,
                "data": {
                    "enrichment_flags": {
                        "is_vip": True,
                        "requires_immediate_attention": context.get("priority") == "critical",
                        "has_history": True,
                        "risk_level": "low"
                    }
                },
                "server": server.value
            }

        elif ability_name == "clarify_question":
            # Check if clarification is needed
            query = context.get("query", "")
            needs_clarification = len(query.split()) < 5 or "?" not in query

            return {
                "success": True,
                "data": {
                    "clarification_needed": needs_clarification,
                    "clarification_questions": [
                        "What specific error message are you seeing?",
                        "When did this issue first occur?"
                    ] if needs_clarification else []
                },
                "server": server.value
            }

        elif ability_name == "extract_answer":
            return {
                "success": True,
                "data": {
                    "extracted_answers": {
                        "error_message": "Invalid credentials",
                        "occurrence_time": "This morning"
                    }
                },
                "server": server.value
            }

        elif ability_name == "store_answer":
            return {
                "success": True,
                "data": {
                    "clarification_answers": context.get("extracted_answers", {})
                },
                "server": server.value
            }

        elif ability_name == "knowledge_base_search":
            # Get query-specific knowledge base results
            query = context.get("query", "")
            parsed_query = context.get("parsed_query", {})
            analysis = self._analyze_query(query)
            category = analysis.get("category", "general")

            # Return different KB articles based on query category
            if category == "billing":
                kb_results = [
                    {
                        "article_id": "KB-BILL-001",
                        "title": "Refund and Return Policy",
                        "confidence": 0.92,
                        "solution": "We offer a 30-day money-back guarantee. To process your refund, please provide your order number and reason for return. Refunds are typically processed within 5-7 business days."
                    },
                    {
                        "article_id": "KB-BILL-002",
                        "title": "Billing Dispute Resolution",
                        "confidence": 0.88,
                        "solution": "If you were charged incorrectly, please contact our billing department with your transaction details. We'll investigate and resolve the issue within 48 hours."
                    }
                ]
            elif category == "product_quality":
                kb_results = [
                    {
                        "article_id": "KB-QUAL-001",
                        "title": "Product Quality Concerns",
                        "confidence": 0.90,
                        "solution": "We apologize for the quality issues. Please provide photos or detailed description of the problem. We can offer a replacement, exchange, or full refund based on your preference."
                    },
                    {
                        "article_id": "KB-QUAL-002",
                        "title": "Quality Guarantee Program",
                        "confidence": 0.85,
                        "solution": "All products come with our quality guarantee. If the product doesn't meet your expectations, contact us within 30 days for a no-questions-asked replacement or refund."
                    }
                ]
            elif category == "account_access":
                kb_results = [
                    {
                        "article_id": "KB-AUTH-001",
                        "title": "Password Reset Procedures",
                        "confidence": 0.95,
                        "solution": "Use the 'Forgot Password' link on the login page. Enter your email, and we'll send a reset link. If you don't receive it within 5 minutes, check your spam folder or contact support."
                    },
                    {
                        "article_id": "KB-AUTH-002",
                        "title": "Account Lockout Resolution",
                        "confidence": 0.87,
                        "solution": "Accounts are temporarily locked after 5 failed login attempts. Wait 30 minutes or contact support to unlock immediately."
                    }
                ]
            elif category == "technical_issue":
                kb_results = [
                    {
                        "article_id": "KB-TECH-001",
                        "title": "App Troubleshooting Guide",
                        "confidence": 0.88,
                        "solution": "Try these steps: 1) Clear app cache and data 2) Restart your device 3) Reinstall the app 4) Ensure you're running the latest version. If the issue persists, contact support with your device model and OS version."
                    },
                    {
                        "article_id": "KB-TECH-002",
                        "title": "Common Error Resolution",
                        "confidence": 0.83,
                        "solution": "Most errors can be resolved by updating to the latest version, checking your internet connection, or clearing browser cache. For persistent issues, please provide the exact error message."
                    }
                ]
            elif category == "api_integration":
                kb_results = [
                    {
                        "article_id": "KB-API-001",
                        "title": "API Authentication Errors",
                        "confidence": 0.93,
                        "solution": "403 Forbidden errors typically indicate invalid API keys or insufficient permissions. Verify your API key is correct, active, and has the required scopes. Regenerate your key if needed."
                    },
                    {
                        "article_id": "KB-API-002",
                        "title": "API Integration Best Practices",
                        "confidence": 0.85,
                        "solution": "Ensure you're including the API key in the Authorization header, using the correct endpoint URL, and following rate limits. Check our API documentation for examples."
                    }
                ]
            elif category == "enhancement":
                kb_results = [
                    {
                        "article_id": "KB-FEAT-001",
                        "title": "Feature Request Process",
                        "confidence": 0.80,
                        "solution": "Thank you for your suggestion! We've added your feature request to our product roadmap. Our team reviews all requests quarterly and prioritizes based on user demand and impact."
                    },
                    {
                        "article_id": "KB-FEAT-002",
                        "title": "Upcoming Features",
                        "confidence": 0.75,
                        "solution": "Check our product roadmap and release notes for upcoming features. You can vote on features you'd like to see and track their development status."
                    }
                ]
            elif category == "account_settings":
                kb_results = [
                    {
                        "article_id": "KB-ACCT-001",
                        "title": "Account Settings Guide",
                        "confidence": 0.91,
                        "solution": "You can update your account settings from the Profile page. Navigate to Settings > Account to change your email, username, password, and preferences."
                    },
                    {
                        "article_id": "KB-ACCT-002",
                        "title": "Profile Management",
                        "confidence": 0.86,
                        "solution": "To modify your profile information, log in and go to Settings. You can update personal details, notification preferences, and privacy settings."
                    }
                ]
            else:
                kb_results = [
                    {
                        "article_id": "KB-GEN-001",
                        "title": "General Support Guide",
                        "confidence": 0.75,
                        "solution": "For assistance with your inquiry, please provide more details about your issue. You can also check our FAQ section or contact our support team directly."
                    }
                ]

            return {
                "success": True,
                "data": {
                    "knowledge_results": kb_results
                },
                "server": server.value
            }

        elif ability_name == "store_data":
            # Get knowledge_results but create a clean copy to avoid circular references
            kb_results = context.get("knowledge_results", [])
            return {
                "success": True,
                "data": {
                    "stored": True,
                    "knowledge_results": kb_results if isinstance(kb_results, list) else []
                },
                "server": server.value
            }

        elif ability_name == "solution_evaluation":
            results = context.get("knowledge_results", [])
            best_score = max([r.get("confidence", 0) for r in results], default=0.0)

            return {
                "success": True,
                "data": {
                    "solution_score": best_score,
                    "selected_solution": results[0] if results else None
                },
                "server": server.value
            }

        elif ability_name == "escalation_decision":
            score = context.get("solution_score", 0.0)
            escalate = score < 0.90

            return {
                "success": True,
                "data": {
                    "escalation_required": escalate,
                    "escalation_reason": "Low confidence score" if escalate else None
                },
                "server": server.value
            }

        elif ability_name == "update_payload":
            return {
                "success": True,
                "data": {
                    "payload_updated": True
                },
                "server": server.value
            }

        elif ability_name == "update_ticket":
            return {
                "success": True,
                "data": {
                    "ticket_status": "resolved",
                    "updated_at": "2025-12-06T10:30:00Z"
                },
                "server": server.value
            }

        elif ability_name == "close_ticket":
            return {
                "success": True,
                "data": {
                    "ticket_status": "closed",
                    "closed_at": "2025-12-06T10:31:00Z"
                },
                "server": server.value
            }

        elif ability_name == "response_generation":
            solution = context.get("selected_solution", {})
            escalated = context.get("escalation_required", False)

            if escalated:
                response = f"Dear {context.get('customer_name', 'Customer')},\n\n" \
                          f"Thank you for contacting support. Your issue has been escalated to our specialist team " \
                          f"for further investigation. Ticket ID: {context.get('ticket_id')}\n\n" \
                          f"Best regards,\nSkylarIQ Support"
            else:
                response = f"Dear {context.get('customer_name', 'Customer')},\n\n" \
                          f"Thank you for contacting support. Here's the solution to your issue:\n\n" \
                          f"{solution.get('solution', 'Please contact support.')}\n\n" \
                          f"Reference: {solution.get('article_id', 'N/A')}\n" \
                          f"Ticket ID: {context.get('ticket_id')}\n\n" \
                          f"Best regards,\nSkylarIQ Support"

            return {
                "success": True,
                "data": {
                    "generated_response": response
                },
                "server": server.value
            }

        elif ability_name == "execute_api_calls":
            return {
                "success": True,
                "data": {
                    "api_results": {
                        "crm_updated": True,
                        "analytics_logged": True
                    }
                },
                "server": server.value
            }

        elif ability_name == "trigger_notifications":
            return {
                "success": True,
                "data": {
                    "notification_status": "sent",
                    "channels": ["email", "sms"],
                    "sent_at": "2025-12-06T10:32:00Z"
                },
                "server": server.value
            }

        elif ability_name == "output_payload":
            return {
                "success": True,
                "data": {
                    "final_output": {
                        "ticket_id": context.get("ticket_id"),
                        "status": context.get("ticket_status", "processed"),
                        "response": context.get("generated_response"),
                        "escalated": context.get("escalation_required", False),
                        "confidence": context.get("solution_score")
                    }
                },
                "server": server.value
            }

        else:
            # Default response for unknown abilities
            return {
                "success": True,
                "data": {
                    "message": f"Executed {ability_name}"
                },
                "server": server.value
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
