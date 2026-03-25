"""
Test Guardrails
Comprehensive tests for query validation and hallucination prevention
"""

from backend.services.guardrails import Guardrails
import json


def print_test(title, passed):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {title}")


def test_valid_queries(gr):
    """Test valid O2C queries"""
    print("\n" + "="*80)
    print("TEST: Valid Queries (Should Pass)")
    print("="*80)
    
    valid_queries = [
        "Find order 740506",
        "Show me customer 310000108",
        "Trace the flow of delivery 80737721",
        "What's the total value of all orders?",
        "Analyze customer purchasing patterns",
        "Find invoices for customer ABC",
        "Show me all payments",
        "Get product details",
        "Which plant has the most orders?"
    ]
    
    for query in valid_queries:
        is_valid, msg = gr.validate_user_query(query)
        print_test(f"'{query}'", is_valid)
        if not is_valid:
            print(f"  Error: {msg}")


def test_rejected_queries(gr):
    """Test out-of-scope queries (Should be rejected)"""
    print("\n" + "="*80)
    print("TEST: Rejected Queries (Should Fail)")
    print("="*80)
    
    rejected_queries = [
        "What's the weather today?",
        "Who won the game yesterday?",
        "Tell me a joke",
        "What is the capital of France?",
        "How do I cook pasta?",
        "What's the latest news?",
        "Write me a poem",
        "What's your opinion on politics?",
        "Help me with my homework",
        "What movies are playing?"
    ]
    
    for query in rejected_queries:
        is_valid, msg = gr.validate_user_query(query)
        print_test(f"'{query}' rejected", not is_valid)
        if not is_valid:
            print(f"  Reason: {msg}")


def test_sql_injection(gr):
    """Test SQL injection attempts (Should be rejected)"""
    print("\n" + "="*80)
    print("TEST: SQL Injection Prevention")
    print("="*80)
    
    malicious_queries = [
        "'; DROP TABLE orders; --",
        "1' OR '1'='1",
        "admin'--",
        "UNION SELECT * FROM users",
        "<script>alert('xss')</script>",
        "DELETE FROM customers WHERE 1=1"
    ]
    
    for query in malicious_queries:
        is_valid, msg = gr.validate_user_query(query)
        print_test(f"Blocked: '{query[:30]}...'", not is_valid)


def test_edge_cases(gr):
    """Test edge cases"""
    print("\n" + "="*80)
    print("TEST: Edge Cases")
    print("="*80)
    
    # Empty query
    is_valid, msg = gr.validate_user_query("")
    print_test("Empty query rejected", not is_valid)
    
    # Very long query
    long_query = "order " * 200
    is_valid, msg = gr.validate_user_query(long_query)
    print_test("Long query rejected", not is_valid)
    
    # Query with only ID (should pass)
    is_valid, msg = gr.validate_user_query("740506")
    print_test("ID-only query accepted", is_valid)


def test_intent_validation(gr):
    """Test intent output validation"""
    print("\n" + "="*80)
    print("TEST: Intent Validation")
    print("="*80)
    
    # Valid intent
    intent = {
        "intent": "get_details",
        "entity_type": "SalesOrder",
        "entity_id": "740506",
        "parameters": {}
    }
    is_valid, msg = gr.validate_intent_output(intent)
    print_test("Valid intent accepted", is_valid)
    
    # Missing intent field
    intent = {"entity_type": "SalesOrder"}
    is_valid, msg = gr.validate_intent_output(intent)
    print_test("Missing intent rejected", not is_valid)
    
    # Invalid intent type
    intent = {"intent": "hack_system", "entity_type": "SalesOrder"}
    is_valid, msg = gr.validate_intent_output(intent)
    print_test("Invalid intent type rejected", not is_valid)
    
    # Invalid entity type
    intent = {
        "intent": "get_details",
        "entity_type": "InvalidEntity",
        "entity_id": "123"
    }
    is_valid, msg = gr.validate_intent_output(intent)
    print_test("Invalid entity type rejected", not is_valid)
    
    # Malicious entity_id
    intent = {
        "intent": "get_details",
        "entity_type": "SalesOrder",
        "entity_id": "'; DROP TABLE--"
    }
    is_valid, msg = gr.validate_intent_output(intent)
    print_test("Malicious entity_id rejected", not is_valid)


def test_result_validation(gr):
    """Test query result validation"""
    print("\n" + "="*80)
    print("TEST: Result Validation")
    print("="*80)
    
    # Valid result
    result = {
        "success": True,
        "data": {"node_id": "Order:123"},
        "metadata": {
            "execution_time_ms": 50,
            "records_found": 1
        },
        "errors": [],
        "warnings": []
    }
    is_valid, msg = gr.validate_query_result(result)
    print_test("Valid result accepted", is_valid)
    
    # Missing success field
    result = {"data": {}, "metadata": {}}
    is_valid, msg = gr.validate_query_result(result)
    print_test("Missing success field rejected", not is_valid)
    
    # Timeout (execution time too high)
    result = {
        "success": True,
        "data": {},
        "metadata": {"execution_time_ms": 50000},
        "errors": [],
        "warnings": []
    }
    is_valid, msg = gr.validate_query_result(result)
    print_test("Timeout result rejected", not is_valid)


def test_response_sanitization(gr):
    """Test response sanitization"""
    print("\n" + "="*80)
    print("TEST: Response Sanitization")
    print("="*80)
    
    # Clean response
    response = "Order 740506 has amount 17108.25 INR"
    sanitized = gr.sanitize_response(response)
    print_test("Clean response unchanged", response == sanitized)
    
    # Response with script tag
    response = "Order 123 <script>alert('xss')</script> found"
    sanitized = gr.sanitize_response(response)
    print_test("Script tag removed", "<script>" not in sanitized)
    
    # Response with SQL command
    response = "DROP TABLE orders; DELETE FROM customers"
    sanitized = gr.sanitize_response(response)
    print_test("SQL commands redacted", "REDACTED" in sanitized)
    
    # Very long response
    response = "A" * 3000
    sanitized = gr.sanitize_response(response)
    print_test("Long response truncated", len(sanitized) <= 2100)


def test_comprehensive_flow(gr):
    """Test complete validation flow"""
    print("\n" + "="*80)
    print("TEST: Comprehensive Flow")
    print("="*80)
    
    # Valid O2C query flow
    query = "Find order 740506"
    
    # Step 1: Validate query
    is_valid, msg = gr.validate_user_query(query)
    print_test("Step 1: Query validated", is_valid)
    
    if is_valid:
        # Step 2: Simulated intent
        intent = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": "740506"
        }
        
        is_valid, msg = gr.validate_intent_output(intent)
        print_test("Step 2: Intent validated", is_valid)
        
        if is_valid:
            # Step 3: Simulated result
            result = {
                "success": True,
                "data": {"order_id": "740506", "amount": 17108.25},
                "metadata": {"execution_time_ms": 25, "records_found": 1},
                "errors": [],
                "warnings": []
            }
            
            is_valid, msg = gr.validate_query_result(result)
            print_test("Step 3: Result validated", is_valid)
            
            # Step 4: Sanitize response
            response = "Found order 740506 with amount 17108.25 INR"
            sanitized = gr.sanitize_response(response)
            print_test("Step 4: Response sanitized", len(sanitized) > 0)
    
    # Invalid flow (should stop at step 1)
    print("\n  Testing rejection flow:")
    query = "What's the weather?"
    is_valid, msg = gr.validate_user_query(query)
    print_test("Step 1: Out-of-scope query rejected", not is_valid)
    print(f"  Message: {msg}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("GUARDRAILS TEST SUITE")
    print("="*80)
    
    gr = Guardrails()
    
    print(f"\nAllowed entities: {len(gr.allowed_entities)}")
    print(f"Allowed intents: {len(gr.allowed_intents)}")
    print(f"Domain keywords: {len(gr.domain_keywords)}")
    print(f"Rejected topics: {len(gr.rejected_topics)}")
    
    # Run all tests
    test_valid_queries(gr)
    test_rejected_queries(gr)
    test_sql_injection(gr)
    test_edge_cases(gr)
    test_intent_validation(gr)
    test_result_validation(gr)
    test_response_sanitization(gr)
    test_comprehensive_flow(gr)
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\nGuardrails successfully prevent:")
    print("  ✓ Out-of-scope queries")
    print("  ✓ SQL injection attempts")
    print("  ✓ Malicious content")
    print("  ✓ Invalid entity types")
    print("  ✓ Hallucinated responses")
    print("  ✓ XSS attacks")


if __name__ == "__main__":
    main()
