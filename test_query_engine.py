"""
Test Query Engine
Comprehensive tests for all query types and edge cases
"""

from backend.services.graph_service import GraphService
from backend.services.query_service import QueryService
from backend.services.query_engine import QueryEngine, EntityNotFoundException, InvalidQueryException
import json


def print_result(title, result):
    """Pretty print query result"""
    print("\n" + "="*80)
    print(f"TEST: {title}")
    print("="*80)
    
    print(f"✓ Success: {result['success']}")
    print(f"⏱  Execution time: {result['metadata']['execution_time_ms']}ms")
    print(f"📊 Records found: {result['metadata']['records_found']}")
    
    if result['errors']:
        print("\n❌ Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['warnings']:
        print("\n⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    if result['success'] and result['data']:
        print("\n📦 Data:")
        print(json.dumps(result['data'], indent=2, default=str)[:500] + "...")


def test_get_details(engine):
    """Test get_details intent"""
    
    # Valid query
    query = {
        "intent": "get_details",
        "entity_type": "SalesOrder",
        "entity_id": "740506"
    }
    result = engine.execute(query)
    print_result("Get Details - Valid Order", result)
    
    # Invalid ID
    query = {
        "intent": "get_details",
        "entity_type": "SalesOrder",
        "entity_id": "INVALID_999"
    }
    result = engine.execute(query)
    print_result("Get Details - Invalid ID (Edge Case)", result)
    
    # Missing entity_id
    query = {
        "intent": "get_details",
        "entity_type": "SalesOrder"
    }
    result = engine.execute(query)
    print_result("Get Details - Missing ID (Edge Case)", result)


def test_search(engine):
    """Test search intent"""
    
    # Normal search
    query = {
        "intent": "search",
        "entity_type": "SalesOrder",
        "entity_id": "740",
        "parameters": {"limit": 5}
    }
    result = engine.execute(query)
    print_result("Search - Partial Match", result)
    
    # Empty results
    query = {
        "intent": "search",
        "entity_id": "NONEXISTENT_XYZ"
    }
    result = engine.execute(query)
    print_result("Search - No Results (Edge Case)", result)


def test_trace_flow(engine):
    """Test trace_flow intent"""
    
    # Valid order
    query = {
        "intent": "trace_flow",
        "entity_type": "SalesOrder",
        "entity_id": "740506"
    }
    result = engine.execute(query)
    print_result("Trace Flow - Complete Order", result)
    
    # Non-existent order
    query = {
        "intent": "trace_flow",
        "entity_type": "SalesOrder",
        "entity_id": "999999"
    }
    result = engine.execute(query)
    print_result("Trace Flow - Non-existent Order (Edge Case)", result)


def test_analytics(engine):
    """Test analytics intent"""
    
    # Valid customer
    query = {
        "intent": "analytics",
        "entity_type": "Customer",
        "entity_id": "310000108"
    }
    result = engine.execute(query)
    print_result("Analytics - Customer Metrics", result)
    
    # Invalid customer
    query = {
        "intent": "analytics",
        "entity_type": "Customer",
        "entity_id": "INVALID"
    }
    result = engine.execute(query)
    print_result("Analytics - Invalid Customer (Edge Case)", result)


def test_aggregate(engine):
    """Test aggregation queries"""
    
    # Count
    query = {
        "intent": "aggregate",
        "entity_type": "SalesOrder",
        "parameters": {"aggregation": "count"}
    }
    result = engine.execute(query)
    print_result("Aggregate - Count Orders", result)
    
    # Sum
    query = {
        "intent": "aggregate",
        "entity_type": "SalesOrder",
        "parameters": {
            "aggregation": "sum",
            "field": "total_net_amount"
        }
    }
    result = engine.execute(query)
    print_result("Aggregate - Sum Order Values", result)
    
    # Average
    query = {
        "intent": "aggregate",
        "entity_type": "SalesOrder",
        "parameters": {
            "aggregation": "avg",
            "field": "total_net_amount"
        }
    }
    result = engine.execute(query)
    print_result("Aggregate - Average Order Value", result)
    
    # Group by
    query = {
        "intent": "aggregate",
        "entity_type": "SalesOrder",
        "parameters": {
            "aggregation": "group_by",
            "field": "transaction_currency"
        }
    }
    result = engine.execute(query)
    print_result("Aggregate - Group by Currency", result)
    
    # Invalid aggregation
    query = {
        "intent": "aggregate",
        "entity_type": "SalesOrder",
        "parameters": {"aggregation": "invalid_agg"}
    }
    result = engine.execute(query)
    print_result("Aggregate - Invalid Aggregation (Edge Case)", result)


def test_detect_missing_links(engine):
    """Test missing link detection"""
    
    query = {
        "intent": "detect_missing_links",
        "entity_type": "SalesOrder"
    }
    result = engine.execute(query)
    print_result("Detect Missing Links - Orders", result)


def test_find_relationship(engine):
    """Test find relationship"""
    
    query = {
        "intent": "find_relationship",
        "entity_type": "SalesOrder",
        "entity_id": "740506",
        "parameters": {"target": "Customer"}
    }
    result = engine.execute(query)
    print_result("Find Relationship - Order to Customer", result)
    
    # No relationships
    query = {
        "intent": "find_relationship",
        "entity_type": "SalesOrder",
        "entity_id": "740506",
        "parameters": {"target": "NonExistentType"}
    }
    result = engine.execute(query)
    print_result("Find Relationship - No Matches (Edge Case)", result)


def test_edge_cases(engine):
    """Test various edge cases"""
    
    # Empty query
    result = engine.execute({})
    print_result("Edge Case - Empty Query", result)
    
    # Missing intent
    result = engine.execute({"entity_type": "SalesOrder"})
    print_result("Edge Case - Missing Intent", result)
    
    # Invalid intent
    result = engine.execute({"intent": "invalid_intent"})
    print_result("Edge Case - Invalid Intent", result)
    
    # Malformed query
    result = engine.execute({"intent": "get_details", "random_field": "value"})
    print_result("Edge Case - Malformed Query", result)


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("QUERY ENGINE TEST SUITE")
    print("="*80)
    
    # Initialize services
    print("\nInitializing services...")
    graph_service = GraphService('dataset/processed_data/graph.gpickle')
    query_service = QueryService(graph_service)
    query_engine = QueryEngine(graph_service, query_service)
    
    print(f"Graph loaded: {graph_service.graph.number_of_nodes()} nodes")
    print(f"Supported intents: {', '.join(query_engine.get_supported_intents())}")
    
    # Run tests
    test_get_details(query_engine)
    test_search(query_engine)
    test_trace_flow(query_engine)
    test_analytics(query_engine)
    test_aggregate(query_engine)
    test_detect_missing_links(query_engine)
    test_find_relationship(query_engine)
    test_edge_cases(query_engine)
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
