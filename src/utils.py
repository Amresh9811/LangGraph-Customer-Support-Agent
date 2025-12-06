"""
Utility functions for the SkylarIQ agent
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime


def setup_logging(log_level: str = "INFO"):
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_stage_logs(logs: list):
    """
    Pretty print stage execution logs.

    Args:
        logs: List of stage execution logs
    """
    print("\n" + "="*80)
    print("STAGE EXECUTION LOGS")
    print("="*80)

    for i, log in enumerate(logs, 1):
        stage = log.get("stage", "Unknown")
        abilities = log.get("abilities", [])
        server = log.get("server", "Unknown")
        timestamp = log.get("timestamp", "N/A")

        print(f"\n{i}. {stage}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Server: {server}")
        print(f"   Abilities: {', '.join(abilities)}")

        # Print success status (using ASCII-safe characters for Windows compatibility)
        success = log.get("success", False)
        if success:
            print(f"   Status: [OK] Success")
        else:
            print(f"   Status: [FAILED] Failed")

    print("\n" + "="*80)


def print_final_output(output: Dict[str, Any]):
    """
    Pretty print final output payload.

    Args:
        output: Output payload dictionary
    """
    print("\n" + "="*80)
    print("FINAL OUTPUT PAYLOAD")
    print("="*80)

    print(f"\nTicket ID: {output.get('ticket_id')}")
    print(f"Customer: {output.get('customer_name')} ({output.get('email')})")
    print(f"Priority: {output.get('priority')}")
    print(f"Status: {output.get('status')}")
    print(f"Escalated: {output.get('escalated')}")

    if output.get('solution_confidence') is not None:
        print(f"Solution Confidence: {output.get('solution_confidence'):.2%}")

    print(f"\nOriginal Query:")
    print(f"  {output.get('original_query')}")

    print(f"\nGenerated Response:")
    print("  " + "\n  ".join(output.get('response', '').split('\n')))

    print(f"\nMetadata:")
    metadata = output.get('metadata', {})
    for key, value in metadata.items():
        print(f"  {key}: {value}")

    print("\n" + "="*80)


def save_output_to_file(output: Dict[str, Any], filename: str):
    """
    Save output payload to JSON file.

    Args:
        output: Output payload dictionary
        filename: Output filename
    """
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nOutput saved to: {filename}")


def format_execution_summary(output: Dict[str, Any]) -> str:
    """
    Format execution summary for display.

    Args:
        output: Output payload dictionary

    Returns:
        Formatted summary string
    """
    summary = []
    summary.append("="*60)
    summary.append("EXECUTION SUMMARY")
    summary.append("="*60)
    summary.append(f"Ticket ID: {output.get('ticket_id')}")
    summary.append(f"Status: {output.get('status')}")
    summary.append(f"Escalated: {'Yes' if output.get('escalated') else 'No'}")

    if output.get('solution_confidence'):
        summary.append(f"Confidence: {output.get('solution_confidence'):.2%}")

    summary.append(f"Stages Executed: {len(output.get('execution_logs', []))}")
    summary.append("="*60)

    return "\n".join(summary)
