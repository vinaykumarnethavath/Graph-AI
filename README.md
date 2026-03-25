# Graph AI

Graph AI is an AI-assisted Order-to-Cash knowledge graph application that combines a FastAPI backend, a React frontend, a NetworkX graph store, and a Groq-powered LLM layer to help you explore business process relationships across customers, sales orders, deliveries, billing documents, journal entries, payments, products, and plants.

## About

Graph AI turns SAP Order-to-Cash data into a connected graph and allows you to:

- ask natural language questions about the business process
- trace document flow across the graph
- inspect node relationships visually
- highlight the exact nodes and edges related to an answer
- validate LLM behavior with guardrails before returning results

The project is designed for explainable graph-based analysis rather than black-box answering. The graph is always the source of truth, and the LLM is used to interpret questions and explain validated results.

## Features

- **AI-powered graph question answering**
- **Interactive graph visualization with answer highlighting**
- **Order-to-Cash flow tracing across linked business entities**
- **Customer, order, delivery, invoice, and payment analytics**
- **Graph-based search, neighborhood exploration, and relationship lookup**
- **Guardrails for query validation, intent validation, and response sanitization**
- **Dataset preprocessing and graph construction pipeline**
- **Support for full-graph rendering with focused answer-path emphasis**

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Frontend UI                    │
│               (React + React Flow)              │
│  - Chat panel                                   │
│  - Graph visualization                          │
│  - Node details                                 │
│  - Answer-based highlighting                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                FastAPI Backend                  │
│             (backend/api/app.py)                │
│  - REST endpoints                               │
│  - Request/response handling                    │
│  - Service orchestration                        │
│  - Error handling                               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                  Guardrails                     │
│       (backend/services/guardrails.py)          │
│  - Query validation                             │
│  - Intent validation                            │
│  - Result validation                            │
│  - Response sanitization                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                   LLM Layer                     │
│         (backend/services/llm_service.py)       │
│  - Groq API integration                         │
│  - Intent extraction                            │
│  - Natural language generation                  │
│  - Conversation management                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                 Query Engine                    │
│       (backend/services/query_engine.py)        │
│  - Intent routing                               │
│  - Structured execution                         │
│  - Analytics and aggregation                    │
│  - Relationship tracing                         │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                 Query Service                   │
│       (backend/services/query_service.py)       │
│  - Business logic                               │
│  - Search and analytics                         │
│  - Flow tracing                                 │
│  - Customer/order insights                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                 Graph Service                   │
│       (backend/services/graph_service.py)       │
│  - NetworkX operations                          │
│  - Node/edge traversal                          │
│  - Path finding                                 │
│  - Subgraph extraction                          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                Knowledge Graph                  │
│   (dataset/processed_data/graph.gpickle)        │
│  - Order-to-Cash entities                       │
│  - Node and edge relationships                  │
│  - Searchable graph structure                   │
└─────────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────────┐
│                Dataset Pipeline                 │
│             (backend/main.py, etc.)             │
│  - Raw data loading                             │
│  - Preprocessing                                │
│  - Relationship analysis                        │
│  - Graph construction                           │
└─────────────────────────────────────────────────┘
```

## Architecture Decisions

### 1. Graph-first answer generation
The system uses the graph as the factual backbone. The LLM does not directly answer from memory. Instead, it:

- interprets the user question
- converts it into a structured graph query
- receives validated graph results
- turns those results into readable language

This keeps answers grounded in actual data.

### 2. Separate frontend and backend responsibilities
The frontend is responsible for visualization and interaction, while the backend handles:

- graph loading
- analytics
- query execution
- LLM orchestration
- guardrail enforcement

This separation improves maintainability and makes it easier to evolve the UI independently.

### 3. Full graph with selective highlighting
Instead of replacing the graph for each query, the application keeps the full graph visible and highlights only the answer-related nodes and edges. This preserves process context and makes the answer visually explainable.

### 4. Structured query engine
A dedicated query engine sits between intent extraction and graph execution. This keeps business logic deterministic and prevents the LLM from bypassing graph constraints.

## Database Choice

Graph AI currently uses **NetworkX** as the graph storage and traversal engine.

### Why NetworkX?

- simple and flexible for in-memory graph operations
- ideal for rapid prototyping and graph algorithm experimentation
- easy to serialize and reload with `graph.gpickle`
- good fit for moderate-size business process graphs

### Why not a graph database yet?

For the current scale and development goals, NetworkX keeps the stack lightweight and easier to iterate on. If the graph grows significantly or needs multi-user persistence, a future migration to Neo4j or another graph database would be a natural next step.

## LLM Prompting Strategy

The LLM layer is deliberately constrained.

### Intent extraction prompt
The model is instructed to:

- stay strictly within the Order-to-Cash domain
- return only structured JSON
- identify the intent, entity type, entity id, and parameters
- reject out-of-scope questions

### Response generation prompt
The model is instructed to:

- use only the provided query results
- avoid hallucinating data
- clearly say when data is unavailable
- explain relationships in plain business language

### Fallback behavior
If the LLM output is malformed or unavailable, the system falls back to simpler keyword-based intent extraction rather than failing silently.

## Guardrails

Graph AI includes multiple guardrail layers to keep behavior safe and relevant.

### Query validation
- blocks out-of-domain prompts
- rejects malformed or unsafe requests

### Intent validation
- checks that LLM-produced intents match the allowed schema
- prevents unsupported query types from reaching execution

### Result validation
- verifies the query engine returned a valid structured result
- ensures the LLM only sees validated data

### Response sanitization
- removes problematic output patterns
- helps keep answers aligned with the graph-backed domain

## Project Structure

After reorganization, the project is intended to follow this structure:

```text
GraphAI/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── config.py
│   ├── run_server.py
│   ├── main.py
│   ├── build_graph.py
│   ├── graph_builder.py
│   ├── graph_analysis.py
│   ├── data_loader.py
│   ├── data_preprocessor.py
│   └── relationship_analyzer.py
├── dataset/
│   ├── sap-o2c-data/
│   ├── processed_data/
│   └── sap-order-to-cash-dataset.zip
├── frontend/
├── tests/
├── README.md
├── requirements.txt
└── .env.example
```

## Setup

### Backend

```bash
pip install -r requirements.txt
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Data Pipeline

### Preprocess dataset

```bash
python backend/main.py
```

### Build graph

```bash
python backend/build_graph.py
```

## Key Output Artifacts

- `dataset/processed_data/graph.gpickle`
- `dataset/processed_data/graph_metadata.json`
- `dataset/processed_data/relationships.json`
- `dataset/processed_data/csv/`
- `dataset/processed_data/parquet/`

## Summary

Graph AI is a graph-first, LLM-assisted application for exploring Order-to-Cash process data with transparency, validation, and explainable visualization.
