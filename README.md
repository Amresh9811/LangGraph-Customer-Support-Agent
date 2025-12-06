# SkylarIQ - LangGraph Customer Support Agent

A production-ready customer support agent built with LangGraph that processes requests through an 11-stage workflow with persistent state management and REST API.

## 🎯 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python main.py
```

Server runs at: **http://localhost:8000**

### 3. Test with ANY Query

```bash
# Interactive mode
python test_single_query.py

# Or test directly
python test_single_query.py "I want refund as the product is not according to the expectation"

# Or use web interface
Open: http://localhost:8000/docs
```

---

## 📋 Overview

**SkylarIQ** processes customer support requests through an 11-stage workflow. Each stage represents a clear phase of processing, with state variables carried forward between stages.

### Key Features

- **11-Stage Workflow**: Complete customer support lifecycle
- **REST API**: Test any query via HTTP endpoints
- **Bulk Processing**: Handle 1 to 100,000+ queries
- **State Persistence**: Maintains state across all workflow stages
- **MCP Integration**: Dual-server architecture (Atlas/Common)
- **Flexible Testing**: Multiple input formats (text, CSV, command line, web UI)

---

## 🔄 Workflow Architecture

```
📥 INTAKE → 🧠 UNDERSTAND → 🛠️ PREPARE → ❓ ASK → ⏳ WAIT →
📚 RETRIEVE → ⚖️ DECIDE → 🔄 UPDATE → ✍️ CREATE → 🏃 DO → ✅ COMPLETE
```

| Stage | Mode | Description | Abilities |
|-------|------|-------------|-----------|
| **INTAKE** 📥 | Deterministic | Accept incoming payload | `accept_payload` |
| **UNDERSTAND** 🧠 | Deterministic | Parse and extract entities | `parse_request_text`, `extract_entities` |
| **PREPARE** 🛠️ | Deterministic | Normalize and enrich data | `normalize_fields`, `enrich_records`, `add_flags_calculations` |
| **ASK** ❓ | Deterministic | Generate clarification questions | `clarify_question` |
| **WAIT** ⏳ | Deterministic | Extract and store answers | `extract_answer`, `store_answer` |
| **RETRIEVE** 📚 | Deterministic | Search knowledge base | `knowledge_base_search`, `store_data` |
| **DECIDE** ⚖️ | **Non-Deterministic** | Evaluate and route solutions | `solution_evaluation`, `escalation_decision`, `update_payload` |
| **UPDATE** 🔄 | Deterministic | Update ticket system | `update_ticket`, `close_ticket` |
| **CREATE** ✍️ | Deterministic | Generate response | `response_generation` |
| **DO** 🏃 | Deterministic | Execute external actions | `execute_api_calls`, `trigger_notifications` |
| **COMPLETE** ✅ | Deterministic | Output final payload | `output_payload` |

---

## 🧪 Testing Guide

### Test Single Query (Simplest Method)

**Interactive Mode:**
```bash
python test_single_query.py
```

**Command Line:**
```bash
python test_single_query.py "I want refund as the product is not according to the expectation"
```

**Web Interface:**
1. Open http://localhost:8000/docs
2. Click `POST /api/tickets` → "Try it out"
3. Enter your query and click "Execute"

### Test Multiple Queries (Bulk Processing)

**From Text File (one query per line):**

Create `my_queries.txt`:
```
I want refund as the product is not according to the expectation
The app keeps crashing when uploading images
How do I reset my password?
```

Run:
```bash
python test_bulk_queries.py --txt my_queries.txt
```

**From CSV File (with details):**

Create `my_queries.csv`:
```csv
query,customer_name,email,priority
I want refund as the product is not good,John Doe,john@example.com,high
The app crashes constantly,Jane Smith,jane@example.com,critical
```

Run:
```bash
python test_bulk_queries.py --csv example_queries.csv
```

**Generate Sample Queries:**
```bash
# Test with 100 sample queries
python test_bulk_queries.py --sample 100

# Test with 100,000 queries in parallel
python test_bulk_queries.py --sample 100000 --batch-size 50 --output results.json
```

### Direct API Calls

**Using curl:**
```bash
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want refund as the product is not according to the expectation",
    "customer_name": "Test User",
    "email": "test@example.com",
    "priority": "high"
  }'
```

---

## 📡 API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Process Single Ticket
```bash
POST http://localhost:8000/api/tickets
```

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "email": "john@example.com",
  "query": "Your question or issue here",
  "priority": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "ticket_id": "TICKET-20251206-133934-059058",
  "status": "closed",
  "escalated": false,
  "response": "Generated customer support response...",
  "solution_confidence": 0.95,
  "processing_time_ms": 2119.40,
  "metadata": {
    "parsed_query": {...},
    "knowledge_results_count": 2
  }
}
```

### Process Batch Tickets
```bash
POST http://localhost:8000/api/tickets/batch
```

Process up to 10 tickets in parallel.

### Get Examples
```bash
GET http://localhost:8000/api/examples
```

### Interactive Documentation
```bash
GET http://localhost:8000/docs        # Swagger UI
GET http://localhost:8000/redoc       # ReDoc
```

---

## 📂 Project Structure

```
langraph/
├── src/
│   ├── agent.py              # Main LangGraph agent orchestrator
│   ├── state.py              # State management and schemas
│   ├── stages.py             # All 11 stage implementations
│   ├── mcp_client.py         # MCP client integration
│   ├── config.py             # Configuration loader
│   └── utils.py              # Utility functions
├── main.py                   # FastAPI REST API server
├── test_single_query.py      # Test single queries (flexible)
├── test_bulk_queries.py      # Test bulk queries (1 to 100k+)
├── run_single_request.py     # Demo script
├── visualize_workflow.py     # Visualize workflow graph
├── example_queries.txt       # Example queries (text format)
├── example_queries.csv       # Example queries (CSV format)
├── config.yaml               # Agent configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
cp .env.example .env
```

Edit `.env`:
```env
ATLAS_MCP_URL=http://localhost:8001
COMMON_MCP_URL=http://localhost:8002
AGENT_NAME=SkylarIQ
LOG_LEVEL=INFO
```

### Agent Configuration (config.yaml)

Defines stages, abilities, and MCP server mappings.

---

## 🚀 Usage Examples

### Run Demo Script

```bash
python run_single_request.py
```

### Visualize Workflow

```bash
python visualize_workflow.py
```

### Test Your Own Query

```python
import asyncio
from src.agent import create_agent
from src.state import InputPayload

async def main():
    agent = await create_agent()

    request = InputPayload(
        customer_name="Jane Doe",
        email="jane@example.com",
        query="I need help resetting my password",
        priority="medium",
        ticket_id="TICKET-001"
    )

    output = await agent.process_request(request)
    print(output.model_dump_json(indent=2))
    await agent.close()

asyncio.run(main())
```

---

## 📊 Example Test Scenarios

### Refund Request
```bash
python test_single_query.py "I want refund as the product is not according to the expectation"
```

### Technical Issue
```bash
python test_single_query.py "The API returns 403 Forbidden error with valid API key"
```

### Password Reset
```bash
python test_single_query.py "I forgot my password and the reset link isn't working"
```

### Billing Issue
```bash
python test_single_query.py "I was charged twice for my subscription this month"
```

---

## 🔧 Bulk Processing Performance

| Queries | Batch Size | Estimated Time |
|---------|-----------|----------------|
| 10 | 10 | ~20 seconds |
| 100 | 50 | ~4 minutes |
| 1,000 | 50 | ~40 minutes |
| 10,000 | 100 | ~6 hours |
| 100,000 | 100 | ~60 hours |

**Optimize with parallel processing:**
```bash
python test_bulk_queries.py --txt queries.txt --batch-size 100 --output results.json
```

---

## 📈 State Management

The agent maintains comprehensive state across all stages:

```python
CustomerSupportState:
    # Input
    customer_name, email, query, priority, ticket_id

    # Processing
    parsed_query, extracted_entities
    normalized_data, enrichment_flags
    clarification_needed, clarification_questions
    knowledge_results

    # Decision
    solution_score, escalation_required, selected_solution

    # Output
    ticket_status, generated_response
    api_results, notification_status

    # Metadata
    stage_logs, current_stage
```

---

## 🐛 Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Try: `uvicorn main:app --port 8080`

### Queries fail to process
- Check server logs for errors
- Ensure all dependencies are installed
- Verify MCP server URLs in `.env`

### Slow processing
- Reduce batch size: `--batch-size 10`
- Check system resources
- Monitor API server logs

### Unicode errors (Windows)
- Scripts automatically handle Windows encoding
- If issues persist, set: `set PYTHONIOENCODING=utf-8`

---

## 🔑 Key Points

✅ **100% Flexible** - Test ANY query, no hardcoded values
✅ **Scalable** - Handle 1 to 100,000+ queries
✅ **Multiple Input Formats** - Text, CSV, JSON, command line, web UI
✅ **Parallel Processing** - Process 50-100 queries simultaneously
✅ **REST API** - Easy integration with other systems
✅ **Comprehensive Reports** - Statistics, confidence scores, processing times

---

## 📝 Quick Reference

| What You Want | Command |
|---------------|---------|
| Start API server | `python main.py` |
| Test 1 query (interactive) | `python test_single_query.py` |
| Test 1 query (direct) | `python test_single_query.py "your query"` |
| Test many queries (text file) | `python test_bulk_queries.py --txt queries.txt` |
| Test many queries (CSV) | `python test_bulk_queries.py --csv queries.csv` |
| Generate samples | `python test_bulk_queries.py --sample 100` |
| Web interface | `http://localhost:8000/docs` |
| Visualize workflow | `python visualize_workflow.py` |
| Run demo | `python run_single_request.py` |

---

## 📚 Example Files Included

- `example_queries.txt` - 20 sample queries (text format)
- `example_queries.csv` - 10 sample queries with customer details (CSV format)

Edit these files or create your own!

---

## 🤝 Support

For issues and questions:
- Check the examples in `examples/`
- Review this README
- Test with provided sample files first

---

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
