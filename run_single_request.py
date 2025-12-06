"""
Run a single customer support request through the SkylarIQ agent.

Usage:
    python run_single_request.py
"""

import asyncio
import json
from pathlib import Path

from src.agent import create_agent
from src.state import InputPayload
from src.config import get_settings
from src.utils import (
    setup_logging,
    print_stage_logs,
    print_final_output,
    save_output_to_file
)


async def main():
    """Run single request demo"""

    # Setup
    settings = get_settings()
    setup_logging(settings.log_level)

    print("\n" + "="*80)
    print("SkylarIQ - Single Request Demo")
    print("="*80)

    # Sample request
    request = {
        "customer_name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "query": "I forgot my password and the reset link isn't working. I've tried multiple times but no email arrives.",
        "priority": "high",
        "ticket_id": "TICKET-DEMO-001"
    }

    print("\nInput Request:")
    print(json.dumps(request, indent=2))

    # Create agent
    print("\nInitializing agent...")
    agent = await create_agent(
        atlas_url=settings.atlas_mcp_url,
        common_url=settings.common_mcp_url
    )

    # Process request
    print("\nProcessing request through 11-stage workflow...")
    print("-"*80)

    input_payload = InputPayload(**request)
    output = await agent.process_request(input_payload)

    # Display results
    output_dict = output.model_dump()

    print("\n" + "="*80)
    print("WORKFLOW EXECUTION COMPLETE")
    print("="*80)

    print_stage_logs(output_dict.get('execution_logs', []))
    print_final_output(output_dict)

    # Save output
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    filename = output_dir / f"single_request_{request['ticket_id']}.json"
    save_output_to_file(output_dict, str(filename))

    # Cleanup
    await agent.close()

    print("\n[SUCCESS] Demo completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
