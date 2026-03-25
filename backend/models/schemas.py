"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class EntityType(str, Enum):
    """Available entity types"""
    CUSTOMER = "Customer"
    SALES_ORDER = "SalesOrder"
    SALES_ORDER_ITEM = "SalesOrderItem"
    DELIVERY = "Delivery"
    DELIVERY_ITEM = "DeliveryItem"
    INVOICE = "Invoice"
    INVOICE_ITEM = "InvoiceItem"
    PAYMENT = "Payment"
    PRODUCT = "Product"
    PLANT = "Plant"


class QueryIntent(str, Enum):
    """Query intent types"""
    SEARCH = "search"
    GET_DETAILS = "get_details"
    TRACE_FLOW = "trace_flow"
    ANALYTICS = "analytics"
    FIND_RELATIONSHIP = "find_relationship"


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(..., description="AI response")
    session_id: Optional[str] = Field(None, description="Session ID")
    query_result: Optional[Dict[str, Any]] = Field(None, description="Structured query result")


class NodeQuery(BaseModel):
    """Query for a specific node"""
    node_id: str = Field(..., description="Node ID")


class SearchQuery(BaseModel):
    """Search query"""
    query: str = Field(..., description="Search query text")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class PathQuery(BaseModel):
    """Path finding query"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    max_paths: int = Field(5, ge=1, le=10, description="Maximum number of paths")
    cutoff: int = Field(10, ge=1, le=20, description="Maximum path length")


class SubgraphQuery(BaseModel):
    """Subgraph query"""
    node_id: str = Field(..., description="Center node ID")
    depth: int = Field(2, ge=1, le=5, description="Depth of subgraph")


class OrderFlowQuery(BaseModel):
    """Order flow query"""
    sales_order_id: str = Field(..., description="Sales order ID")


class CustomerAnalyticsQuery(BaseModel):
    """Customer analytics query"""
    customer_id: str = Field(..., description="Customer ID")


class DocumentFlowQuery(BaseModel):
    """Document flow query"""
    document_id: str = Field(..., description="Document ID")
    document_type: EntityType = Field(..., description="Document type")


class GraphStats(BaseModel):
    """Graph statistics"""
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    is_directed: bool


class NodeResponse(BaseModel):
    """Node response"""
    node_id: str
    node_type: str
    attributes: Dict[str, Any]
    in_degree: int
    out_degree: int


class EdgeResponse(BaseModel):
    """Edge response"""
    source: str
    target: str
    relationship: str
    direction: str
    attributes: Optional[Dict[str, Any]] = None


class SubgraphResponse(BaseModel):
    """Subgraph response"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    total_nodes: int
    total_edges: int


class OrderFlowResponse(BaseModel):
    """Order flow response"""
    order: Optional[Dict[str, Any]]
    items: List[Dict[str, Any]]
    deliveries: List[Dict[str, Any]]
    invoices: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    customer: Optional[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
