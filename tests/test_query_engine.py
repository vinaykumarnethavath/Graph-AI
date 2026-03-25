"""
Query Engine Tests
Tests query correctness and execution
"""

import pytest


@pytest.mark.query
class TestQueryEngineBasics:
    """Test basic query engine operations"""
    
    def test_get_details_valid(self, query_engine, sample_order_id):
        """Test getting details for valid entity"""
        query = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": sample_order_id
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert result["data"] is not None
        assert result["data"]["node"]["sales_order"] == sample_order_id
        assert result["metadata"]["records_found"] == 1
        assert len(result["errors"]) == 0
    
    def test_get_details_invalid_id(self, query_engine):
        """Test getting details for non-existent entity"""
        query = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": "INVALID_999"
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()
    
    def test_search(self, query_engine):
        """Test search functionality"""
        query = {
            "intent": "search",
            "entity_type": "SalesOrder",
            "entity_id": "740",
            "parameters": {"limit": 5}
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert isinstance(result["data"], list)
        assert result["metadata"]["records_found"] >= 0
    
    def test_search_no_results(self, query_engine):
        """Test search with no results"""
        query = {
            "intent": "search",
            "entity_id": "NONEXISTENT_XYZ_12345"
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert len(result["data"]) == 0
        assert "No results found" in result["warnings"]


@pytest.mark.query
class TestFlowTracing:
    """Test order flow tracing"""
    
    def test_trace_flow_valid_order(self, query_engine, sample_order_id):
        """Test tracing flow for valid order"""
        query = {
            "intent": "trace_flow",
            "entity_type": "SalesOrder",
            "entity_id": sample_order_id
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "order" in result["data"]
        assert "items" in result["data"]
        assert "deliveries" in result["data"]
        assert result["data"]["order"] is not None
    
    def test_trace_flow_missing_links(self, query_engine, sample_order_id):
        """Test flow tracing detects missing links"""
        query = {
            "intent": "trace_flow",
            "entity_type": "SalesOrder",
            "entity_id": sample_order_id
        }
        
        result = query_engine.execute(query)
        
        # Should have warnings about missing links
        if not result["data"].get("invoices"):
            assert any("invoice" in w.lower() for w in result["warnings"])
    
    def test_trace_flow_invalid_order(self, query_engine):
        """Test tracing flow for non-existent order"""
        query = {
            "intent": "trace_flow",
            "entity_type": "SalesOrder",
            "entity_id": "999999"
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0


@pytest.mark.query
class TestAggregations:
    """Test aggregation queries"""
    
    def test_aggregate_count(self, query_engine):
        """Test count aggregation"""
        query = {
            "intent": "aggregate",
            "entity_type": "SalesOrder",
            "parameters": {"aggregation": "count"}
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "count" in result["data"]
        assert result["data"]["count"] > 0
    
    def test_aggregate_sum(self, query_engine):
        """Test sum aggregation"""
        query = {
            "intent": "aggregate",
            "entity_type": "SalesOrder",
            "parameters": {
                "aggregation": "sum",
                "field": "total_net_amount"
            }
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "sum" in result["data"]
        assert result["data"]["sum"] >= 0
    
    def test_aggregate_average(self, query_engine):
        """Test average aggregation"""
        query = {
            "intent": "aggregate",
            "entity_type": "SalesOrder",
            "parameters": {
                "aggregation": "avg",
                "field": "total_net_amount"
            }
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "average" in result["data"]
    
    def test_aggregate_group_by(self, query_engine):
        """Test group by aggregation"""
        query = {
            "intent": "aggregate",
            "entity_type": "SalesOrder",
            "parameters": {
                "aggregation": "group_by",
                "field": "transaction_currency"
            }
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "groups" in result["data"]
        assert isinstance(result["data"]["groups"], dict)


@pytest.mark.query
class TestMissingLinkDetection:
    """Test missing link detection"""
    
    def test_detect_missing_links(self, query_engine):
        """Test detecting incomplete records"""
        query = {
            "intent": "detect_missing_links",
            "entity_type": "SalesOrder"
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "total_checked" in result["data"]
        assert "missing_links" in result["data"]
        assert "completeness_rate" in result["data"]
        assert 0 <= result["data"]["completeness_rate"] <= 100


@pytest.mark.query
class TestAnalytics:
    """Test analytics queries"""
    
    def test_customer_analytics(self, query_engine, sample_customer_id):
        """Test customer analytics"""
        query = {
            "intent": "analytics",
            "entity_type": "Customer",
            "entity_id": sample_customer_id
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert "customer" in result["data"]
        assert "total_orders" in result["data"]
        assert "total_order_value" in result["data"]


@pytest.mark.query
class TestExecutionMetadata:
    """Test query execution metadata"""
    
    def test_execution_time_tracked(self, query_engine, sample_order_id):
        """Test execution time is tracked"""
        query = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": sample_order_id
        }
        
        result = query_engine.execute(query)
        
        assert "execution_time_ms" in result["metadata"]
        assert result["metadata"]["execution_time_ms"] > 0
        assert result["metadata"]["execution_time_ms"] < 30000  # Less than 30s
    
    def test_records_found_counted(self, query_engine):
        """Test records found is counted correctly"""
        query = {
            "intent": "search",
            "entity_id": "740",
            "parameters": {"limit": 5}
        }
        
        result = query_engine.execute(query)
        
        assert "records_found" in result["metadata"]
        assert result["metadata"]["records_found"] == len(result["data"])
