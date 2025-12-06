"""
Simple script to test a single query with the SkylarIQ API.
No hardcoded values - completely flexible!

Usage:
    python test_single_query.py
"""

import httpx
import asyncio
import json
from datetime import datetime


API_URL = "http://localhost:8000"


async def test_query(query: str, customer_name: str = None, email: str = None, priority: str = "medium"):
    """
    Test a single query against the API.

    Args:
        query: Your question/issue (the only required field!)
        customer_name: Optional customer name (auto-generated if not provided)
        email: Optional email (auto-generated if not provided)
        priority: Optional priority (default: medium)
    """
    # Auto-generate customer details if not provided
    if not customer_name:
        customer_name = "Test Customer"

    if not email:
        email = "test@example.com"

    # Generate unique ticket ID
    ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    # Build request
    request_data = {
        "customer_name": customer_name,
        "email": email,
        "query": query,
        "priority": priority,
        "ticket_id": ticket_id
    }

    print("\n" + "="*80)
    print("TESTING QUERY")
    print("="*80)
    print(f"\nQuery: {query}")
    print(f"Priority: {priority}")
    print(f"Ticket ID: {ticket_id}")
    print("\nSending request to API...")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/api/tickets",
                json=request_data
            )

            if response.status_code == 200:
                result = response.json()

                print("\n" + "="*80)
                print("[SUCCESS] TICKET PROCESSED")
                print("="*80)
                print(f"\nTicket ID: {result['ticket_id']}")
                print(f"Status: {result['status']}")
                print(f"Escalated: {'Yes' if result['escalated'] else 'No'}")

                if result.get('solution_confidence'):
                    print(f"Solution Confidence: {result['solution_confidence']*100:.1f}%")

                print(f"Processing Time: {result['processing_time_ms']:.2f}ms")

                print("\n" + "-"*80)
                print("GENERATED RESPONSE:")
                print("-"*80)
                print(result['response'])
                print("-"*80)

                # Show metadata
                print("\nMETADATA:")
                print(f"  Intent: {result['metadata'].get('parsed_query', {}).get('intent', 'N/A')}")
                print(f"  Category: {result['metadata'].get('parsed_query', {}).get('category', 'N/A')}")
                print(f"  Knowledge Results: {result['metadata'].get('knowledge_results_count', 0)}")

                return result
            else:
                print(f"\n[ERROR] Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None

    except httpx.ConnectError:
        print("\n[ERROR] Cannot connect to API server!")
        print("Make sure the server is running:")
        print("  python main.py")
        return None
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        return None


async def interactive_mode():
    """Run in interactive mode - ask user for queries"""
    print("\n" + "="*80)
    print("SKYLARIQ - INTERACTIVE QUERY TESTER")
    print("="*80)
    print("\nTest ANY query with the API - no hardcoded values!")
    print("Just type your query and press Enter.\n")

    while True:
        print("\n" + "="*80)
        query = input("\nEnter your query (or 'quit' to exit): ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("\nExiting...")
            break

        if len(query) < 10:
            print("[ERROR] Query must be at least 10 characters long. Try again.")
            continue

        # Optional: Ask for priority
        priority = input("Enter priority (low/medium/high/critical) [medium]: ").strip() or "medium"

        # Optional: Ask for customer details
        use_custom = input("Use custom name/email? (y/n) [n]: ").strip().lower()
        customer_name = None
        email = None

        if use_custom == 'y':
            customer_name = input("Customer name [Test Customer]: ").strip() or None
            email = input("Email [test@example.com]: ").strip() or None

        # Process query
        await test_query(query, customer_name, email, priority)

        # Ask if user wants to test another
        another = input("\n\nTest another query? (y/n) [y]: ").strip().lower()
        if another == 'n':
            break

    print("\n" + "="*80)
    print("Thank you for testing!")
    print("="*80 + "\n")


async def main():
    """Main entry point"""
    import sys

    # Check if query is provided as command line argument
    if len(sys.argv) > 1:
        # Direct mode: query provided as argument
        query = ' '.join(sys.argv[1:])
        await test_query(query)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
