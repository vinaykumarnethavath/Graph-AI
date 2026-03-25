"""
API Endpoint Tests
Tests all FastAPI endpoints
"""

import pytest


@pytest.mark.api
class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, api_client):
        """Test health endpoint returns 200"""
        response = api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data


@pytest.mark.api
class TestGraphEndpoints:
    """Test graph-related endpoints"""
    
    def test_get_graph_stats(self, api_client):
        """Test graph statistics endpoint"""
        response = api_client.get("/api/graph/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_nodes" in data
        assert "total_edges" in data
        assert "node_types" in data
        assert data["total_nodes"] > 0
        assert data["total_edges"] > 0
    
    def test_get_node_valid(self, api_client, sample_order_id):
        """Test getting a valid node"""
        response = api_client.post("/api/graph/node", json={
            "node_id": f"SalesOrder:{sample_order_id}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "node_id" in data
        assert "node_type" in data
        assert data["node_type"] == "SalesOrder"
    
    def test_get_node_invalid(self, api_client):
        """Test getting non-existent node"""
        response = api_client.post("/api/graph/node", json={
            "node_id": "SalesOrder:INVALID_999"
        })
        assert response.status_code == 404
    
    def test_get_node_neighbors(self, api_client, sample_order_id):
        """Test getting node neighbors"""
        response = api_client.get(
            f"/api/graph/node/SalesOrder:{sample_order_id}/neighbors"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "predecessors" in data or "successors" in data
    
    def test_get_node_edges(self, api_client, sample_order_id):
        """Test getting node edges"""
        response = api_client.get(
            f"/api/graph/node/SalesOrder:{sample_order_id}/edges"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "edges" in data
        assert "total" in data
    
    def test_search_nodes(self, api_client):
        """Test node search"""
        response = api_client.post("/api/graph/search", json={
            "query": "740",
            "limit": 5
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total" in data
    
    def test_get_subgraph(self, api_client, sample_order_id):
        """Test subgraph extraction"""
        response = api_client.post("/api/graph/subgraph", json={
            "node_id": f"SalesOrder:{sample_order_id}",
            "depth": 2
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0


@pytest.mark.api
class TestQueryEndpoints:
    """Test query-related endpoints"""
    
    def test_order_flow(self, api_client, sample_order_id):
        """Test order flow endpoint"""
        response = api_client.post("/api/query/order-flow", json={
            "sales_order_id": sample_order_id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "order" in data
        assert "items" in data
        assert data["order"] is not None
    
    def test_order_flow_invalid(self, api_client):
        """Test order flow with invalid ID"""
        response = api_client.post("/api/query/order-flow", json={
            "sales_order_id": "INVALID_999"
        })
        assert response.status_code == 404
    
    def test_customer_analytics(self, api_client, sample_customer_id):
        """Test customer analytics endpoint"""
        response = api_client.post("/api/query/customer-analytics", json={
            "customer_id": sample_customer_id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "customer" in data
        assert "total_orders" in data
    
    def test_customer_orders(self, api_client, sample_customer_id):
        """Test getting customer orders"""
        response = api_client.get(f"/api/query/customer/{sample_customer_id}/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert "total" in data
    
    def test_delivery_details(self, api_client, sample_delivery_id):
        """Test delivery details endpoint"""
        response = api_client.get(f"/api/query/delivery/{sample_delivery_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "delivery" in data


@pytest.mark.api
@pytest.mark.llm
class TestChatEndpoint:
    """Test chat endpoint with LLM integration"""
    
    def test_chat_valid_query(self, api_client, sample_order_id):
        """Test chat with valid O2C query"""
        response = api_client.post("/api/chat", json={
            "message": f"Find order {sample_order_id}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert "query_result" in data
    
    def test_chat_out_of_scope(self, api_client):
        """Test chat with out-of-scope query"""
        response = api_client.post("/api/chat", json={
            "message": "What's the weather today?"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        # Should contain rejection message
        assert "Order-to-Cash" in data["response"]
    
    def test_chat_malicious(self, api_client):
        """Test chat with malicious query"""
        response = api_client.post("/api/chat", json={
            "message": "'; DROP TABLE orders; --"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        # Should be rejected
        assert "malicious" in data["response"].lower() or "Order-to-Cash" in data["response"]
    
    def test_chat_clear(self, api_client):
        """Test clearing chat history"""
        response = api_client.post("/api/chat/clear")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.api
class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self, api_client):
        """Test accessing invalid endpoint"""
        response = api_client.get("/api/invalid")
        assert response.status_code == 404
    
    def test_missing_required_field(self, api_client):
        """Test request with missing required field"""
        response = api_client.post("/api/graph/node", json={})
        assert response.status_code == 422  # Validation error
    
    def test_invalid_json(self, api_client):
        """Test request with invalid JSON"""
        response = api_client.post(
            "/api/graph/node",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
