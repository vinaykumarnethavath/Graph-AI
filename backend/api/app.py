"""
FastAPI Application
Main backend server for the Order-to-Cash Graph AI
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.services import GraphService, QueryService, LLMService
from backend.services.query_engine import QueryEngine
from backend.services.guardrails import Guardrails, OutOfScopeException, InvalidOutputException
from backend.models import (
    ChatMessage,
    ChatResponse,
    NodeQuery,
    SearchQuery,
    PathQuery,
    SubgraphQuery,
    OrderFlowQuery,
    CustomerAnalyticsQuery,
    DocumentFlowQuery,
    GraphStats,
    ErrorResponse
)


# Global service instances
graph_service: GraphService = None
query_service: QueryService = None
llm_service: LLMService = None
guardrails: Guardrails = None
query_engine: QueryEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global graph_service, query_service, llm_service, query_engine, guardrails
    
    # Startup: Initialize services
    print("Starting up application...")
    graph_service = GraphService(settings.graph_path)
    query_service = QueryService(graph_service)
    llm_service = LLMService(settings.groq_api_key)
    query_engine = QueryEngine(graph_service, query_service)
    guardrails = Guardrails()
    print("Services initialized successfully")
    print("Guardrails enabled: Query validation active") 
    
    yield
    
    # Shutdown
    print("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered Order-to-Cash Knowledge Graph API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve static files from backend/static
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")





# Dependency to get services
def get_graph_service() -> GraphService:
    return graph_service


def get_query_service() -> QueryService:
    return query_service


def get_llm_service() -> LLMService:
    return llm_service


def get_query_engine() -> QueryEngine:
    return query_engine


def get_guardrails() -> Guardrails:
    return guardrails


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


# Graph statistics
@app.get("/api/graph/stats", response_model=GraphStats)
async def get_graph_stats(service: GraphService = Depends(get_graph_service)):
    """Get graph statistics"""
    try:
        stats = service.get_graph_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get full graph
@app.get("/api/graph/full")
async def get_full_graph(service: GraphService = Depends(get_graph_service)):
    """Get all nodes and edges in the graph with robust serialization"""
    try:
        nodes = []
        edges = []
        
        # Get all nodes with safe attribute conversion
        for node_id, node_data in service.graph.nodes(data=True):
            node_item: Dict[str, Any] = {'node_id': str(node_id)}
            # Ensure all attributes are JSON serializable
            for k, v in node_data.items():
                if isinstance(v, (int, float, bool, list, dict, type(None))):
                    node_item[str(k)] = v
                else:
                    node_item[str(k)] = str(v)
            nodes.append(node_item)
        
        # Get all edges with support for MultiDiGraph and DiGraph
        edge_view = service.graph.edges(data=True)
        for edge in edge_view:
            # Handle (u, v, data) or (u, v, key, data)
            if len(edge) == 3:
                u, v, data = edge
            elif len(edge) == 4:
                u, v, _, data = edge
            else:
                continue
                
            edge_item: Dict[str, Any] = {
                'source': str(u),
                'target': str(v)
            }
            # Ensure all attributes are JSON serializable
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (int, float, bool, list, dict, type(None))):
                        edge_item[str(k)] = v
                    else:
                        edge_item[str(k)] = str(v)
            edges.append(edge_item)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
    except Exception as e:
        import traceback
        print(f"Error in get_full_graph: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Get node by ID
@app.post("/api/graph/node")
async def get_node(query: NodeQuery, service: GraphService = Depends(get_graph_service)):
    """Get a node by ID"""
    try:
        node = service.get_node(query.node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node {query.node_id} not found")
        return node
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get node neighbors
@app.get("/api/graph/node/{node_id}/neighbors")
async def get_node_neighbors(node_id: str, direction: str = "both", 
                              service: GraphService = Depends(get_graph_service)):
    """Get neighbors of a node"""
    try:
        neighbors = service.get_node_neighbors(node_id, direction)
        return neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get node edges
@app.get("/api/graph/node/{node_id}/edges")
async def get_node_edges(node_id: str, service: GraphService = Depends(get_graph_service)):
    """Get all edges connected to a node"""
    try:
        edges = service.get_edges_for_node(node_id)
        return {"edges": edges, "total": len(edges)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search nodes
@app.post("/api/graph/search")
async def search_nodes(query: SearchQuery, service: QueryService = Depends(get_query_service)):
    """Search nodes by text query"""
    try:
        entity_types = [et.value for et in query.entity_types] if query.entity_types else None
        results = service.search_entities(query.query, entity_types, query.limit)
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Find paths
@app.post("/api/graph/paths")
async def find_paths(query: PathQuery, service: GraphService = Depends(get_graph_service)):
    """Find paths between two nodes"""
    try:
        paths = service.find_paths(query.source, query.target, query.max_paths, query.cutoff)
        return {"paths": paths, "total": len(paths)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get subgraph
@app.post("/api/graph/subgraph")
async def get_subgraph(query: SubgraphQuery, service: GraphService = Depends(get_graph_service)):
    """Get subgraph around a node"""
    try:
        subgraph = service.get_subgraph(query.node_id, query.depth)
        return subgraph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get order flow
@app.post("/api/query/order-flow")
async def get_order_flow(query: OrderFlowQuery, service: GraphService = Depends(get_graph_service)):
    """Get complete order-to-cash flow for a sales order"""
    try:
        flow = service.get_order_flow(query.sales_order_id)
        if not flow:
            raise HTTPException(status_code=404, detail=f"Order {query.sales_order_id} not found")
        return flow
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get customer analytics
@app.post("/api/query/customer-analytics")
async def get_customer_analytics(query: CustomerAnalyticsQuery, 
                                  service: QueryService = Depends(get_query_service)):
    """Get analytics for a customer"""
    try:
        analytics = service.get_customer_analytics(query.customer_id)
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Customer {query.customer_id} not found")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Trace document flow
@app.post("/api/query/document-flow")
async def trace_document_flow(query: DocumentFlowQuery, 
                               service: QueryService = Depends(get_query_service)):
    """Trace the complete flow of a document"""
    try:
        flow = service.trace_document_flow(query.document_id, query.document_type.value)
        if not flow:
            raise HTTPException(status_code=404, 
                                detail=f"{query.document_type} {query.document_id} not found")
        return flow
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get customer orders
@app.get("/api/query/customer/{customer_id}/orders")
async def get_customer_orders(customer_id: str, service: QueryService = Depends(get_query_service)):
    """Get all orders for a customer"""
    try:
        orders = service.get_customer_orders(customer_id)
        return {"orders": orders, "total": len(orders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get delivery details
@app.get("/api/query/delivery/{delivery_id}")
async def get_delivery_details(delivery_id: str, service: QueryService = Depends(get_query_service)):
    """Get complete delivery details"""
    try:
        details = service.get_delivery_details(delivery_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Delivery {delivery_id} not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get invoice details
@app.get("/api/query/invoice/{billing_document}")
async def get_invoice_details(billing_document: str, service: QueryService = Depends(get_query_service)):
    """Get complete invoice details"""
    try:
        details = service.get_invoice_details(billing_document)
        if not details:
            raise HTTPException(status_code=404, detail=f"Invoice {billing_document} not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoint with QueryEngine and Guardrails
@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, 
               graph_svc: GraphService = Depends(get_graph_service),
               llm_svc: LLMService = Depends(get_llm_service),
               qe: QueryEngine = Depends(get_query_engine),
               gr: Guardrails = Depends(get_guardrails)):
    """Chat with the graph AI using QueryEngine with Guardrails"""
    try:
        # STEP 1: Validate user query (Guardrail)
        is_valid, error_msg = gr.validate_user_query(message.message)
        if not is_valid:
            return ChatResponse(
                response=error_msg + "\n\n" + gr.get_rejection_message(),
                session_id=message.session_id,
                query_result=None
            )
        
        # Get graph stats for context
        graph_stats = graph_svc.get_graph_stats()
        
        # Extract intent from LLM
        intent = llm_svc.extract_query_intent(message.message, graph_stats)
        
        # STEP 2: Check if LLM marked query as out of scope
        if intent.get('intent') == 'out_of_scope':
            return ChatResponse(
                response=gr.get_rejection_message(),
                session_id=message.session_id,
                query_result=None
            )
        
        # STEP 3: Validate intent output (Guardrail)
        is_valid, error_msg = gr.validate_intent_output(intent)
        if not is_valid:
            return ChatResponse(
                response=f"Invalid query format: {error_msg}",
                session_id=message.session_id,
                query_result=None
            )
        
        # Execute query using QueryEngine
        query_result = qe.execute(intent)
        
        # STEP 4: Validate query result (Guardrail)
        is_valid, error_msg = gr.validate_query_result(query_result)
        if not is_valid:
            return ChatResponse(
                response=f"Query result validation failed: {error_msg}",
                session_id=message.session_id,
                query_result=None
            )
        
        # Check if query was successful
        if query_result["success"]:
            # Generate natural language response
            response_text = llm_svc.generate_response(
                message.message,
                query_result["data"],
                context=f"Warnings: {query_result['warnings']}" if query_result['warnings'] else None,
                session_id=message.session_id
            )
            
            # STEP 5: Sanitize response (Guardrail)
            response_text = gr.sanitize_response(response_text)
            
            # Add warnings to response if present
            if query_result["warnings"]:
                response_text += "\n\n⚠️ " + "\n⚠️ ".join(query_result["warnings"])
            
            return ChatResponse(
                response=response_text,
                session_id=message.session_id,
                query_result=query_result["data"]
            )
        else:
            # Query failed, return error message
            error_msg = "I encountered an issue: " + "; ".join(query_result["errors"])
            return ChatResponse(
                response=error_msg,
                session_id=message.session_id,
                query_result=None
            )
        
    except Exception as e:
        # Fallback to general chat
        try:
            response_text = llm_svc.chat(message.message, graph_stats)
            return ChatResponse(
                response=response_text,
                session_id=message.session_id
            )
        except Exception as chat_error:
            raise HTTPException(status_code=500, detail=str(chat_error))


# Clear chat history
@app.post("/api/chat/clear")
async def clear_chat(llm_svc: LLMService = Depends(get_llm_service)):
    """Clear chat history"""
    try:
        llm_svc.clear_history()
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Catch-all route to serve index.html for React Router
# This MUST be at the end of the file to avoid intercepting other routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # If the path is an API path, let FastAPI handle it normally
    if full_path.startswith("api/") or full_path.startswith("health"):
        # If we reached here, it means the API route was not found
        raise HTTPException(status_code=404, detail="API route not found")
    
    # Check if the file exists in static dir
    file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Fallback to index.html for React routing
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "Graph AI Backend is Running. Frontend not yet built."}
