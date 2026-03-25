"""
Edge Case Tests
Tests various edge cases and error conditions
"""

import pytest


@pytest.mark.edge
class TestInvalidInputs:
    """Test handling of invalid inputs"""
    
    def test_empty_query(self, query_engine):
        """Test empty query"""
        result = query_engine.execute({})
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    def test_missing_intent(self, query_engine):
        """Test query with missing intent"""
        query = {"entity_type": "SalesOrder"}
        
        result = query_engine.execute(query)
        
        assert result["success"] is False
        assert "intent" in result["errors"][0].lower()
    
    def test_invalid_intent(self, query_engine):
        """Test query with invalid intent"""
        query = {"intent": "invalid_intent"}
        
        result = query_engine.execute(query)
        
        assert result["success"] is False
    
    def test_invalid_entity_type(self, query_engine):
        """Test query with invalid entity type - should still execute"""
        query = {
            "intent": "get_details",
            "entity_type": "InvalidEntity",
            "entity_id": "123"
        }
        
        result = query_engine.execute(query)
        
        # May fail due to invalid node ID format
        assert "success" in result


@pytest.mark.edge
class TestNullAndEmptyValues:
    """Test handling of null and empty values"""
    
    def test_search_empty_results(self, query_engine):
        """Test search returning no results"""
        query = {
            "intent": "search",
            "entity_id": "NONEXISTENT_ENTITY_999999"
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        assert len(result["data"]) == 0
        assert result["metadata"]["records_found"] == 0
    
    def test_aggregate_with_nulls(self, query_engine):
        """Test aggregation handles null values"""
        query = {
            "intent": "aggregate",
            "entity_type": "SalesOrder",
            "parameters": {
                "aggregation": "sum",
                "field": "total_net_amount"
            }
        }
        
        result = query_engine.execute(query)
        
        # Should handle nulls gracefully
        assert result["success"] is True
        assert "sum" in result["data"]


@pytest.mark.edge
class TestBoundaryConditions:
    """Test boundary conditions"""
    
    def test_large_limit(self, query_engine):
        """Test search with very large limit"""
        query = {
            "intent": "search",
            "entity_id": "7",
            "parameters": {"limit": 10000}
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is True
        # Should be capped internally
    
    def test_zero_depth_subgraph(self, graph_service, sample_order_id):
        """Test subgraph with depth 0"""
        subgraph = graph_service.get_subgraph(f"SalesOrder:{sample_order_id}", depth=0)
        
        # Should at least contain the node itself
        assert len(subgraph["nodes"]) >= 1


@pytest.mark.edge
class TestDuplicateData:
    """Test handling of duplicate data"""
    
    def test_deduplication(self, query_engine):
        """Test that search deduplicates results"""
        query = {
            "intent": "search",
            "entity_id": "740",
            "parameters": {"limit": 20}
        }
        
        result = query_engine.execute(query)
        
        if result["data"]:
            # Check no duplicate node_ids
            node_ids = [item["node_id"] for item in result["data"]]
            assert len(node_ids) == len(set(node_ids))


@pytest.mark.edge
class TestCircularReferences:
    """Test handling of circular references"""
    
    def test_subgraph_with_limit(self, graph_service, sample_order_id):
        """Test subgraph extraction doesn't loop infinitely"""
        # High depth that could cause issues if not handled
        subgraph = graph_service.get_subgraph(f"SalesOrder:{sample_order_id}", depth=5)
        
        # Should complete without infinite loop
        assert "nodes" in subgraph
        assert "edges" in subgraph


@pytest.mark.edge
class TestSpecialCharacters:
    """Test handling of special characters"""
    
    def test_search_special_chars(self, query_engine):
        """Test search with special characters"""
        query = {
            "intent": "search",
            "entity_id": "!@#$%"
        }
        
        result = query_engine.execute(query)
        
        # Should handle gracefully
        assert "success" in result
    
    def test_entity_id_with_colons(self, query_engine):
        """Test entity ID containing colons"""
        query = {
            "intent": "get_details",
            "entity_type": "Payment",
            "entity_id": "1000:2025:123"  # Valid format for payments
        }
        
        result = query_engine.execute(query)
        
        # Should handle multi-part IDs
        assert "success" in result


@pytest.mark.edge
class TestConcurrency:
    """Test concurrent operations"""
    
    def test_multiple_queries_same_entity(self, query_engine, sample_order_id):
        """Test multiple queries for same entity"""
        query = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": sample_order_id
        }
        
        # Execute multiple times
        results = [query_engine.execute(query) for _ in range(3)]
        
        # All should succeed with same data
        assert all(r["success"] for r in results)
        assert all(r["data"]["node"]["sales_order"] == sample_order_id for r in results)


@pytest.mark.edge
class TestErrorRecovery:
    """Test error recovery"""
    
    def test_partial_failure_handling(self, query_engine):
        """Test handling of partial failures"""
        # Query that might have missing data
        query = {
            "intent": "trace_flow",
            "entity_type": "SalesOrder",
            "entity_id": "740506"
        }
        
        result = query_engine.execute(query)
        
        # Should succeed even if some parts are missing
        assert result["success"] is True
        # Should have warnings about missing parts
        if not result["data"].get("invoices"):
            assert len(result["warnings"]) > 0
    
    def test_malformed_query_graceful_failure(self, query_engine):
        """Test graceful failure for malformed queries"""
        query = {
            "intent": "get_details",
            "random_field": "random_value"
            # Missing required entity_id
        }
        
        result = query_engine.execute(query)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        # Should not crash, should return structured error
        assert "metadata" in result
