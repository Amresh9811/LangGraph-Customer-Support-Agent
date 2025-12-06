"""
SkylarIQ - FastAPI Server
REST API for processing customer support requests through LangGraph workflow.

Usage:
    uvicorn main:app --reload --port 8000

Endpoints:
    POST /api/tickets - Process a customer support ticket
    GET /health - Health check
    GET /docs - Interactive API documentation
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr

from src.agent import create_agent, SkylarIQAgent
from src.state import InputPayload, OutputPayload
from src.config import get_settings
from src.utils import setup_logging


# Global agent instance
agent: Optional[SkylarIQAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global agent

    # Startup: Initialize agent
    settings = get_settings()
    setup_logging(settings.log_level)

    logging.info("Starting SkylarIQ API server...")
    agent = await create_agent(
        atlas_url=settings.atlas_mcp_url,
        common_url=settings.common_mcp_url
    )
    logging.info("Agent initialized successfully")

    yield

    # Shutdown: Cleanup
    if agent:
        await agent.close()
        logging.info("Agent closed successfully")


# FastAPI app
app = FastAPI(
    title="SkylarIQ API",
    description="Customer Support Agent powered by LangGraph",
    version="1.0.0",
    lifespan=lifespan
)


# Request/Response models
class TicketRequest(BaseModel):
    """API request model for creating a ticket"""
    customer_name: str = Field(..., description="Customer name", min_length=1, max_length=200)
    email: EmailStr = Field(..., description="Customer email address")
    query: str = Field(..., description="Customer query or issue description", min_length=10, max_length=5000)
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    ticket_id: Optional[str] = Field(None, description="Optional ticket ID (auto-generated if not provided)")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "customer_name": "Alice Williams",
                "email": "alice.w@company.com",
                "query": "I'm trying to integrate your API with our CRM system, but I keep getting 403 Forbidden errors. I've checked the API key multiple times and it seems correct. Can you help?",
                "priority": "high",
                "ticket_id": "TICKET-2025-101"
            }]
        }
    }


class TicketResponse(BaseModel):
    """API response model"""
    success: bool
    ticket_id: str
    status: str
    escalated: bool
    response: str
    solution_confidence: Optional[float] = None
    metadata: dict
    processing_time_ms: float


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SkylarIQ API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Main ticket processing endpoint
@app.post("/api/tickets", response_model=TicketResponse, tags=["Tickets"])
async def process_ticket(request: TicketRequest):
    """
    Process a customer support ticket through the 11-stage workflow.

    The workflow stages are:
    1. INTAKE - Accept and validate payload
    2. UNDERSTAND - Parse and extract entities
    3. PREPARE - Normalize and enrich data
    4. ASK - Determine if clarification is needed
    5. WAIT - Extract and store answers (conditional)
    6. RETRIEVE - Search knowledge base
    7. DECIDE - Evaluate solutions and escalation
    8. UPDATE - Update ticket in external system
    9. CREATE - Generate customer response
    10. DO - Execute external actions
    11. COMPLETE - Output final payload
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    try:
        start_time = datetime.utcnow()

        # Generate ticket ID if not provided
        ticket_id = request.ticket_id or f"TICKET-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Create input payload
        input_payload = InputPayload(
            customer_name=request.customer_name,
            email=request.email,
            query=request.query,
            priority=request.priority,
            ticket_id=ticket_id
        )

        # Process request through workflow
        logging.info(f"Processing ticket: {ticket_id}")
        output = await agent.process_request(input_payload)

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Build response
        response = TicketResponse(
            success=True,
            ticket_id=output.ticket_id,
            status=output.status,
            escalated=output.escalated,
            response=output.response,
            solution_confidence=output.solution_confidence,
            metadata=output.metadata,
            processing_time_ms=round(processing_time, 2)
        )

        logging.info(f"Ticket {ticket_id} processed successfully in {processing_time:.2f}ms")
        return response

    except Exception as e:
        logging.error(f"Error processing ticket: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing ticket: {str(e)}"
        )


# Batch processing endpoint
@app.post("/api/tickets/batch", tags=["Tickets"])
async def process_tickets_batch(requests: list[TicketRequest]):
    """
    Process multiple tickets in parallel.

    Note: This endpoint processes tickets concurrently for better performance.
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    if len(requests) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 tickets can be processed in a single batch"
        )

    try:
        start_time = datetime.utcnow()

        # Process all tickets concurrently
        tasks = []
        for req in requests:
            ticket_id = req.ticket_id or f"TICKET-{datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')}"
            input_payload = InputPayload(
                customer_name=req.customer_name,
                email=req.email,
                query=req.query,
                priority=req.priority,
                ticket_id=ticket_id
            )
            tasks.append(agent.process_request(input_payload))

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build responses
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append({
                    "success": False,
                    "ticket_id": requests[i].ticket_id or "UNKNOWN",
                    "error": str(result)
                })
            else:
                responses.append({
                    "success": True,
                    "ticket_id": result.ticket_id,
                    "status": result.status,
                    "escalated": result.escalated,
                    "solution_confidence": result.solution_confidence
                })

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000

        return {
            "success": True,
            "total_tickets": len(requests),
            "processing_time_ms": round(processing_time, 2),
            "results": responses
        }

    except Exception as e:
        logging.error(f"Error processing batch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch: {str(e)}"
        )


# Example endpoint to get sample requests
@app.get("/api/examples", tags=["Examples"])
async def get_examples():
    """Get example ticket requests for testing"""
    return {
        "examples": [
            {
                "customer_name": "Alice Williams",
                "email": "alice.w@company.com",
                "query": "I'm trying to integrate your API with our CRM system, but I keep getting 403 Forbidden errors. I've checked the API key multiple times and it seems correct. Can you help?",
                "priority": "high",
                "ticket_id": "TICKET-2025-101"
            },
            {
                "customer_name": "Bob Martinez",
                "email": "bob.martinez@tech.co",
                "query": "The mobile app keeps crashing whenever I try to upload images larger than 5MB. This is blocking my workflow.",
                "priority": "medium",
                "ticket_id": "TICKET-2025-102"
            },
            {
                "customer_name": "Carol Anderson",
                "email": "carol@enterprise.net",
                "query": "Our security team needs information about your data encryption standards and compliance certifications. This is urgent for our vendor assessment.",
                "priority": "critical",
                "ticket_id": "TICKET-2025-103"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
