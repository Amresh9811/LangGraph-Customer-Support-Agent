"""
Bulk Query Processor - Test thousands of queries efficiently.

This script can:
1. Process queries from a CSV file
2. Process queries from a JSON file
3. Process a list of queries in parallel
4. Generate detailed reports

Usage:
    # From CSV file:
    python test_bulk_queries.py --csv queries.csv

    # From JSON file:
    python test_bulk_queries.py --json queries.json

    # From text file (one query per line):
    python test_bulk_queries.py --txt queries.txt

    # Process sample queries:
    python test_bulk_queries.py --sample 10
"""

import httpx
import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import argparse


API_URL = "http://localhost:8000"


async def process_single_query(
    query: str,
    customer_name: str = "Test Customer",
    email: str = "test@example.com",
    priority: str = "medium",
    ticket_id: str = None
) -> Dict[str, Any]:
    """
    Process a single query through the API.

    Returns:
        Result dictionary with success status and details
    """
    if not ticket_id:
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    request_data = {
        "customer_name": customer_name,
        "email": email,
        "query": query,
        "priority": priority,
        "ticket_id": ticket_id
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/api/tickets",
                json=request_data
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "query": query,
                    "ticket_id": result['ticket_id'],
                    "status": result['status'],
                    "escalated": result['escalated'],
                    "confidence": result.get('solution_confidence'),
                    "processing_time_ms": result['processing_time_ms'],
                    "response": result['response']
                }
            else:
                return {
                    "success": False,
                    "query": query,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e)
        }


async def process_queries_batch(queries: List[Dict[str, str]], batch_size: int = 10) -> List[Dict[str, Any]]:
    """
    Process multiple queries in batches.

    Args:
        queries: List of query dictionaries with keys: query, customer_name, email, priority
        batch_size: Number of queries to process in parallel (default: 10)

    Returns:
        List of results
    """
    results = []
    total = len(queries)

    print(f"\n{'='*80}")
    print(f"PROCESSING {total} QUERIES")
    print(f"Batch size: {batch_size}")
    print(f"{'='*80}\n")

    for i in range(0, total, batch_size):
        batch = queries[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} queries)...")

        # Process batch in parallel
        tasks = []
        for q in batch:
            task = process_single_query(
                query=q.get('query'),
                customer_name=q.get('customer_name', 'Test Customer'),
                email=q.get('email', 'test@example.com'),
                priority=q.get('priority', 'medium'),
                ticket_id=q.get('ticket_id')
            )
            tasks.append(task)

        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

        # Show progress
        success_count = sum(1 for r in batch_results if r['success'])
        print(f"  [OK] Batch {batch_num} complete: {success_count}/{len(batch)} successful")

    return results


def load_queries_from_csv(filepath: str) -> List[Dict[str, str]]:
    """Load queries from CSV file. Expected columns: query, customer_name, email, priority"""
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'query' in row and row['query'].strip():
                queries.append({
                    'query': row['query'].strip(),
                    'customer_name': row.get('customer_name', 'Test Customer'),
                    'email': row.get('email', 'test@example.com'),
                    'priority': row.get('priority', 'medium')
                })
    return queries


def load_queries_from_json(filepath: str) -> List[Dict[str, str]]:
    """Load queries from JSON file. Expected format: list of objects with query field"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        queries = []
        for item in data:
            if isinstance(item, dict) and 'query' in item:
                queries.append(item)
            elif isinstance(item, str):
                queries.append({'query': item})
        return queries
    else:
        raise ValueError("JSON file must contain a list of queries")


def load_queries_from_txt(filepath: str) -> List[Dict[str, str]]:
    """Load queries from text file (one query per line)"""
    queries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and len(line) >= 10:
                queries.append({'query': line})
    return queries


def generate_sample_queries(count: int) -> List[Dict[str, str]]:
    """Generate sample queries for testing"""
    sample_queries = [
        "I want a refund as the product is not according to the expectation",
        "How do I reset my password? The reset link is not working",
        "The app keeps crashing when I try to upload images",
        "I need information about your data encryption standards",
        "Can I change my username in the account settings?",
        "I was charged twice for my subscription this month",
        "The API is returning 403 Forbidden errors with my valid API key",
        "Please add dark mode support to the mobile app",
        "My account has been locked and I cannot log in",
        "How long does shipping take for international orders?",
        "The website is very slow and pages take forever to load",
        "I need to cancel my subscription immediately",
        "Can you help me integrate your API with our CRM system?",
        "The mobile app is not syncing with the web version",
        "I forgot which email address I used to register",
        "Is there a way to export my data in CSV format?",
        "The payment failed but I was still charged",
        "How do I upgrade to the premium plan?",
        "I'm getting error 500 when trying to save changes",
        "Can you provide documentation for the REST API?"
    ]

    queries = []
    for i in range(count):
        query_text = sample_queries[i % len(sample_queries)]
        queries.append({
            'query': f"{query_text} (Test #{i+1})",
            'priority': ['low', 'medium', 'high', 'critical'][i % 4]
        })

    return queries


def generate_report(results: List[Dict[str, Any]], output_file: str = None):
    """Generate detailed report from results"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful

    if successful > 0:
        avg_time = sum(r.get('processing_time_ms', 0) for r in results if r['success']) / successful
        escalated_count = sum(1 for r in results if r.get('escalated', False))
        avg_confidence = sum(r.get('confidence', 0) for r in results if r.get('confidence')) / successful
    else:
        avg_time = 0
        escalated_count = 0
        avg_confidence = 0

    report = f"""
{'='*80}
BULK PROCESSING REPORT
{'='*80}

SUMMARY:
  Total Queries: {total}
  Successful: {successful} ({successful/total*100:.1f}%)
  Failed: {failed} ({failed/total*100:.1f}%)

PERFORMANCE:
  Average Processing Time: {avg_time:.2f}ms
  Total Processing Time: {sum(r.get('processing_time_ms', 0) for r in results)/1000:.2f}s

RESULTS:
  Escalated: {escalated_count} ({escalated_count/total*100:.1f}%)
  Average Confidence: {avg_confidence*100:.1f}%

{'='*80}
"""

    print(report)

    # Save detailed results to JSON
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'successful': successful,
                    'failed': failed,
                    'avg_processing_time_ms': avg_time,
                    'escalated_count': escalated_count,
                    'avg_confidence': avg_confidence
                },
                'results': results
            }, f, indent=2)

        print(f"[OK] Detailed results saved to: {output_file}\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bulk Query Processor for SkylarIQ API')
    parser.add_argument('--csv', help='Path to CSV file with queries')
    parser.add_argument('--json', help='Path to JSON file with queries')
    parser.add_argument('--txt', help='Path to text file with queries (one per line)')
    parser.add_argument('--sample', type=int, help='Generate N sample queries for testing')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for parallel processing (default: 10)')
    parser.add_argument('--output', help='Output file for results (JSON format)')

    args = parser.parse_args()

    # Load queries
    queries = []

    if args.csv:
        print(f"Loading queries from CSV: {args.csv}")
        queries = load_queries_from_csv(args.csv)
    elif args.json:
        print(f"Loading queries from JSON: {args.json}")
        queries = load_queries_from_json(args.json)
    elif args.txt:
        print(f"Loading queries from TXT: {args.txt}")
        queries = load_queries_from_txt(args.txt)
    elif args.sample:
        print(f"Generating {args.sample} sample queries")
        queries = generate_sample_queries(args.sample)
    else:
        print("Error: Please specify input source (--csv, --json, --txt, or --sample)")
        parser.print_help()
        return

    if not queries:
        print("Error: No queries found!")
        return

    print(f"Loaded {len(queries)} queries\n")

    # Process queries
    results = await process_queries_batch(queries, batch_size=args.batch_size)

    # Generate report
    output_file = args.output or f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    generate_report(results, output_file)


if __name__ == "__main__":
    asyncio.run(main())
