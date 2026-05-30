# 🔌 API Reference Documentation

Complete reference for all AndroMate AI Agent API endpoints.

**Base URLs:**
- Chat API: `http://localhost:8000`
- RAG API: `http://localhost:8001`
- Metrics: `http://localhost:8000/metrics` (Prometheus)

**Authentication:** Bearer token in `Authorization` header  
**Last Updated:** May 30, 2026

---

## Table of Contents

1. [Authentication](#-authentication)
2. [Chat API](#-chat-api)
3. [RAG API](#-rag-api)
4. [Health & Metrics](#-health--metrics)
5. [Response Formats](#-response-formats)
6. [Error Handling](#-error-handling)
7. [Code Examples](#-code-examples)

---

## 🔐 Authentication

### Bearer Token

All endpoints require authentication via Bearer token in the `Authorization` header.

**Header Format:**
```
Authorization: Bearer YOUR_API_KEY
```

**Example:**
```bash
# Example using Chat API endpoint
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer sk-your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "Send a message", "type_intent": "workflow_generation"}'
```

### Getting Your API Key

1. Check `.env` file for `API_KEY` variable
2. Or retrieve from environment:
   ```bash
   grep "API_KEY=" .env
   ```

### Invalid Token Response

```json
{
  "detail": "Not authenticated",
  "status": 401
}
```

---

## 💬 Chat API

**Base URL:** `http://localhost:8000`

### 1. Generate Workflow

**Endpoint:** `POST /chat`

Generate an Android automation workflow from natural language description.

**Request:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Send an SMS to +33612345678 with the message hello world",
    "type_intent": "workflow_generation",
    "provider": "openai"
  }'
```

**Request Body:**

```json
{
  "query": "Send an SMS to +33612345678 with the message hello world",
  "type_intent": "workflow_generation",
  "workflow": null,
  "provider": "openai"
}
```

**Parameters:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `query` | string | ✅ | User request | "Send a message on WhatsApp" |
| `type_intent` | string | ❌ | Intent type | "workflow_generation", "workflow_correction", "qa" |
| `workflow` | object | ❌ | Existing workflow (for correction) | `{"tasks": [...]}` |
| `provider` | string | ❌ | LLM provider override | "openai", "ollama", "openrouter" |

**Success Response (200 OK):**

```json
{
  "intent": "workflow_generation",
  "task_names": ["SendSMS"],
  "result": {
    "workflow": {
      "tasks": [
        {
          "name": "SendSMS",
          "msisdn": "+33612345678",
          "message_body": "hello world"
        }
      ],
      "explanation": "This workflow sends an SMS message to the specified phone number using the SendSMS task."
    },
    "validation_passed": true,
    "retry_count": 0,
    "errors_found": []
  },
  "metadata": {
    "plan": {
      "required_tasks": ["SendSMS"]
    },
    "plan_confidence": 0.95,
    "plan_ambiguities": [],
    "context_length": 2048,
    "intent_source": "user_choice",
    "validation_passed": true,
    "retry_count": 0,
    "errors_found": [],
    "processor_status": "success"
  }
}
```

**Error Responses:**

```json
// 400 - Invalid request
{
  "detail": "Invalid LLM provider: xyz"
}

// 401 - Authentication failed
{
  "detail": "Invalid API key"
}

// 503 - Service unavailable
{
  "detail": "Vector database temporarily unavailable"
}

// 504 - Timeout
{
  "detail": "Request processing timeout"
}
```

**Caching:** Responses cached for 1 hour based on query + intent + workflow hash

---

### 2. Correct Workflow

**Endpoint:** `POST /chat`

Fix or improve an existing workflow based on user feedback.

**Request:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Also send a notification after sending the message",
    "type_intent": "workflow_correction",
    "workflow": {
      "tasks": [
        {"name": "open_app", "app": "WhatsApp", "action": "open"},
        {"name": "send_message", "message": "Hello", "action": "send"}
      ]
    }
  }'
```

**Request Body:**

```json
{
  "query": "Also wait for 5 seconds after sending the SMS",
  "type_intent": "workflow_correction",
  "workflow": {
    "tasks": [
      {"name": "SendSMS", "msisdn": "+33612345678", "message_body": "Hello"}
    ]
  }
}
```

**Response:**

```json
{
  "intent": "workflow_correction",
  "task_names": ["SendSMS", "sleep"],
  "result": {
    "workflow": {
      "tasks": [
        {"name": "SendSMS", "msisdn": "+33612345678", "message_body": "Hello"},
        {"name": "sleep", "duration_ms": 5000}
      ]
    },
    "validation_passed": true,
    "retry_count": 0,
    "errors_found": []
  },
  "metadata": {...}
}
```

---

### 3. Ask Questions (Q&A)

**Endpoint:** `POST /chat`

Ask questions about available tasks and workflows.

**Request:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What tasks are available for SMS communication?",
    "type_intent": "qa"
  }'
```

**Request Body:**

```json
{
  "query": "What tasks are available for SMS communication?",
  "type_intent": "qa"
}
```

**Response:**

```json
{
  "intent": "qa",
  "task_names": [],
  "result": "SMS communication tasks available:\n\n1. **SendSMS** - Send plain-text SMS messages\n   - Parameters: msisdn (E.164 format), message_body (max 100 chars)\n   - Example: {\"name\": \"SendSMS\", \"msisdn\": \"+33612345678\", \"message_body\": \"Hello\"}\n\n2. **wait-sms** - Wait for an incoming SMS message\n   - Used to capture received SMS in workflows\n\nNote: Phone number must be in E.164 format (e.g. +33612345678)",
  "metadata": {
    "context_length": 1024,
    "intent_source": "auto_detected"
  }
}
```

---

### 4. Metrics

**Endpoint:** `GET /metrics`

Prometheus metrics for monitoring.

**Request:**

```bash
curl http://localhost:8000/metrics
```

**Response (Prometheus format):**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/chat", method="POST", status="200"} 1523.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/chat",le="0.1"} 12.0
http_request_duration_seconds_bucket{endpoint="/chat",le="0.5"} 98.0
http_request_duration_seconds_bucket{endpoint="/chat",le="1.0"} 156.0

# HELP cache_hits_total Total cache hits
# TYPE cache_hits_total counter
cache_hits_total 325.0

# HELP active_requests Active requests
# TYPE active_requests gauge
active_requests 2.0
```

---

## 📚 RAG API

**Base URL:** `http://localhost:8001`

### 1. Upload Single Document

**Endpoint:** `POST /add_document`

Upload and ingest a single Markdown document with automatic pipeline processing:
- Document cleaning and validation
- Text chunking with overlap
- Embedding generation
- Vector storage in Qdrant

Handles updates if document already exists (idempotent).

**Request:**

```bash
curl -X POST http://localhost:8001/add_document \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@send-sms.md" \
  -F "doc_type=task_doc"
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file (multipart) | ✅ | Markdown file to upload (.md extension required) |
| `doc_type` | string | ❌ | Document type: `task_doc`, `workflow_doc`, `app_doc`, or `general_doc`. If omitted, inferred from filename |

**Supported Document Types:**
- `task_doc` - Android task documentation (e.g., send-sms.md, http-request.md)
- `workflow_doc` - Workflow examples and patterns
- `app_doc` - App-specific guides
- `general_doc` - General documentation

**Success Response (200 OK):**

```json
{
  "document_id": "send-sms",
  "filename": "send-sms.md",
  "doc_type": "task_doc",
  "message": "Document processed and stored",
  "chunks_created": 12,
  "vectors_uploaded": 12,
  "is_update": false,
  "collection": "andromate_docs",
  "processing_time_seconds": 2.34
}
```

**Error Responses:**

```json
// 400 - Invalid file format
{
  "detail": "Only .md files are supported"
}

// 413 - File too large
{
  "detail": "File too large. Maximum size: 50MB, received: 65.42MB"
}

// 503 - Qdrant unavailable
{
  "detail": "Cannot connect to Qdrant"
}
```

**Constraints:**
- Maximum file size: 50MB
- File encoding: UTF-8 required
- File extension: .md only

---

### 2. Upload Multiple Documents (Batch)

**Endpoint:** `POST /add_documents`

Upload and ingest multiple Markdown documents in a single request.

**Request:**

```bash
curl -X POST http://localhost:8001/add_documents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "files=@send-sms.md" \
  -F "files=@http-request.md" \
  -F "files=@dns-lookup.md"
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | file[] (multipart) | ✅ | Multiple markdown files to upload (.md extension required) |

**Success Response (200 OK):**

```json
{
  "message": "Batch processing completed",
  "total_documents": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "send-sms.md",
      "status": "success",
      "chunks_created": 12,
      "vectors_uploaded": 12
    },
    {
      "filename": "http-request.md",
      "status": "success",
      "chunks_created": 18,
      "vectors_uploaded": 18
    },
    {
      "filename": "dns-lookup.md",
      "status": "success",
      "chunks_created": 8,
      "vectors_uploaded": 8
    }
  ],
  "total_chunks": 38,
  "total_vectors": 38,
  "processing_time_seconds": 6.78
}
```

**Error Response (Partial Failure):**

```json
{
  "message": "Batch processing completed with errors",
  "total_documents": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "filename": "send-sms.md",
      "status": "success",
      "chunks_created": 12
    },
    {
      "filename": "invalid.pdf",
      "status": "failed",
      "error": "Only .md files are supported"
    }
  ]
}
```

---

### 3. Health Check

**Endpoint:** `GET /health`

Check RAG API status and verify Qdrant connectivity.

**Request:**

```bash
curl http://localhost:8001/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Success Response (200 OK):**

```json
{
  "status": "healthy",
  "qdrant": "available"
}
```

**Error Response (503):**

```json
{
  "status": "unhealthy",
  "error": "Cannot connect to Qdrant at localhost:6333"
}
```

---

## 🏥 Health & Metrics

### Endpoint: `/health`

**RAG API only** - Check RAG API status and Qdrant connectivity.

```bash
curl http://localhost:8001/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Endpoint: `/metrics`

Available on both APIs for Prometheus monitoring.

**Chat API metrics:**

```bash
curl http://localhost:8000/metrics | head -20
```

**RAG API metrics:**

```bash
curl http://localhost:8001/metrics | head -20
```

---

## 📋 Response Formats

### Success Response

```json
{
  "status": 200,
  "data": {...},
  "message": "Success",
  "timestamp": "2026-05-30T10:15:22.123456Z"
}
```

### Error Response

```json
{
  "status": 400,
  "error": "Invalid Request",
  "detail": "Query parameter is required",
  "timestamp": "2026-05-30T10:15:22.123456Z"
}
```

### Pagination (Future)

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 47,
    "total_pages": 5
  }
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid API key |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Endpoint doesn't exist |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Qdrant/LLM down |
| 504 | Gateway Timeout | LLM took too long |

### Error Response Format

```json
{
  "detail": "Error message here",
  "status": 400,
  "error_code": "INVALID_REQUEST"
}
```

### Common Errors

**Invalid API Key:**
```json
{"detail": "Invalid API key", "status": 401}
```

**Qdrant Connection Error:**
```json
{"detail": "Vector database temporarily unavailable", "status": 503}
```

**LLM Timeout:**
```json
{"detail": "Request processing timeout after 120s", "status": 504}
```

---

## 💻 Code Examples

### Python

```python
import requests
import json

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

def chat(query, intent="workflow_generation"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "type_intent": intent,
        "provider": "openai"
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None

# Usage
result = chat("Send SMS to +33612345678 with message hello")
print(json.dumps(result, indent=2))
```

### JavaScript

```javascript
const API_KEY = "your-api-key-here";
const BASE_URL = "http://localhost:8000";

async function chat(query, intent = "workflow_generation") {
  const headers = {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  };

  const payload = {
    query: query,
    type_intent: intent,
    provider: "openai"
  };

  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      return await response.json();
    } else {
      console.error(`Error: ${response.status}`);
      console.error(await response.json());
      return null;
    }
  } catch (error) {
    console.error("Request failed:", error);
    return null;
  }
}

// Usage
chat("Send SMS to +33612345678 with message hello").then(result => {
  console.log(JSON.stringify(result, null, 2));
});
```

### cURL

```bash
# Set API key
API_KEY="your-api-key-here"
BASE_URL="http://localhost:8000"

# Generate workflow
curl -X POST $BASE_URL/chat \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Send SMS to +33612345678 with message hello",
    "type_intent": "workflow_generation"
  }' | jq .

# Get metrics
curl http://localhost:8000/metrics | jq .```
```

### Bash Script

```bash
#!/bin/bash

API_KEY="${API_KEY:-your-api-key-here}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

chat_api() {
  local query="$1"
  local intent="${2:-workflow_generation}"
  
  curl -X POST "$BASE_URL/chat" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\", \"type_intent\": \"$intent\"}" \
    -s | jq .
}

# Usage
chat_api "Send SMS to +33612345678 with message hello world"```
```

---

## 📊 Rate Limiting

Currently not enforced, but planned for production:

- **Limit:** 100 requests/minute per API key
- **Response:** 429 Too Many Requests when exceeded
- **Retry-After:** Header indicating when to retry

---

## 📝 API Documentation (Auto-generated)

Access Swagger UI at: `http://localhost:8000/docs`

Access ReDoc at: `http://localhost:8000/redoc`

---

**Questions?** Check [README.md](README.md) or [INSTALLATION.md](INSTALLATION.md)
