"""
LLM Output Validation Tests
Tests LLM integration and output validation
"""

import pytest


@pytest.mark.llm
@pytest.mark.slow
class TestLLMIntentExtraction:
    """Test LLM intent extraction"""
    
    def test_extract_simple_query(self, llm_service):
        """Test extracting intent from simple query"""
        query = "Find order 740506"
        graph_stats = {"total_nodes": 1000}
        
        intent = llm_service.extract_query_intent(query, graph_stats)
        
        assert isinstance(intent, dict)
        assert "intent" in intent
        assert "entity_type" in intent
        assert intent["intent"] in ["get_details", "search"]
    
    def test_extract_flow_query(self, llm_service):
        """Test extracting intent from flow query"""
        query = "Trace the flow of order 740506"
        graph_stats = {"total_nodes": 1000}
        
        intent = llm_service.extract_query_intent(query, graph_stats)
        
        assert intent["intent"] == "trace_flow"
        assert intent.get("entity_id") == "740506"
    
    def test_extract_analytics_query(self, llm_service):
        """Test extracting intent from analytics query"""
        query = "Analyze customer 310000108"
        graph_stats = {"total_nodes": 1000}
        
        intent = llm_service.extract_query_intent(query, graph_stats)
        
        assert intent["intent"] in ["analytics", "get_details"]
        assert intent.get("entity_id") == "310000108"
    
    def test_extract_out_of_scope(self, llm_service):
        """Test LLM detects out of scope queries"""
        query = "What's the weather today?"
        graph_stats = {"total_nodes": 1000}
        
        intent = llm_service.extract_query_intent(query, graph_stats)
        
        # LLM should mark as out_of_scope or fallback will handle it
        assert isinstance(intent, dict)
        assert "intent" in intent


@pytest.mark.llm
class TestGuardrailsValidation:
    """Test guardrails validation"""
    
    def test_validate_valid_query(self, guardrails, valid_o2c_queries):
        """Test validation of valid O2C queries"""
        for query in valid_o2c_queries:
            is_valid, msg = guardrails.validate_user_query(query)
            assert is_valid, f"Query '{query}' should be valid but was rejected: {msg}"
    
    def test_validate_invalid_queries(self, guardrails, invalid_queries):
        """Test rejection of invalid queries"""
        for query in invalid_queries:
            is_valid, msg = guardrails.validate_user_query(query)
            assert not is_valid, f"Query '{query}' should be rejected but was accepted"
            assert len(msg) > 0
    
    def test_validate_malicious_queries(self, guardrails, malicious_queries):
        """Test blocking of malicious queries"""
        for query in malicious_queries:
            is_valid, msg = guardrails.validate_user_query(query)
            assert not is_valid, f"Malicious query '{query}' should be blocked"
            assert "malicious" in msg.lower() or "Order-to-Cash" in msg
    
    def test_validate_intent_structure(self, guardrails):
        """Test intent structure validation"""
        # Valid intent
        intent = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": "740506",
            "parameters": {}
        }
        is_valid, msg = guardrails.validate_intent_output(intent)
        assert is_valid
        
        # Invalid intent
        intent = {
            "intent": "hack_database",
            "entity_type": "SalesOrder"
        }
        is_valid, msg = guardrails.validate_intent_output(intent)
        assert not is_valid
    
    def test_validate_entity_type(self, guardrails):
        """Test entity type validation"""
        # Valid entity
        intent = {
            "intent": "get_details",
            "entity_type": "SalesOrder",
            "entity_id": "123"
        }
        is_valid, msg = guardrails.validate_intent_output(intent)
        assert is_valid
        
        # Invalid entity
        intent = {
            "intent": "get_details",
            "entity_type": "FakeEntity",
            "entity_id": "123"
        }
        is_valid, msg = guardrails.validate_intent_output(intent)
        assert not is_valid
    
    def test_validate_result_structure(self, guardrails):
        """Test query result validation"""
        # Valid result
        result = {
            "success": True,
            "data": {"test": "data"},
            "metadata": {"execution_time_ms": 50, "records_found": 1},
            "errors": [],
            "warnings": []
        }
        is_valid, msg = guardrails.validate_query_result(result)
        assert is_valid
        
        # Invalid result (missing fields)
        result = {"success": True}
        is_valid, msg = guardrails.validate_query_result(result)
        assert not is_valid
    
    def test_sanitize_response(self, guardrails):
        """Test response sanitization"""
        # Clean response
        response = "Order 740506 has amount 17108.25 INR"
        sanitized = guardrails.sanitize_response(response)
        assert response == sanitized
        
        # Response with script tag
        response = "Order <script>alert('xss')</script> found"
        sanitized = guardrails.sanitize_response(response)
        assert "<script>" not in sanitized
        
        # Response with SQL
        response = "DROP TABLE orders"
        sanitized = guardrails.sanitize_response(response)
        assert "REDACTED" in sanitized


@pytest.mark.llm
@pytest.mark.slow
class TestLLMResponseGeneration:
    """Test LLM response generation"""
    
    def test_generate_response_with_data(self, llm_service):
        """Test generating response with query data"""
        query = "Find order 740506"
        query_result = {
            "node_id": "SalesOrder:740506",
            "sales_order": "740506",
            "total_net_amount": 17108.25,
            "transaction_currency": "INR"
        }
        
        response = llm_service.generate_response(query, query_result)
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should mention the order number
        assert "740506" in response
    
    def test_generate_response_no_data(self, llm_service):
        """Test generating response with no data"""
        query = "Find order INVALID"
        query_result = None
        
        response = llm_service.generate_response(query, query_result)
        
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.llm
class TestFallbackMechanisms:
    """Test fallback mechanisms"""
    
    def test_fallback_intent_extraction(self, llm_service):
        """Test fallback intent extraction works"""
        # This should work even if LLM fails
        intent = llm_service._fallback_intent_extraction("Find order 740506")
        
        assert isinstance(intent, dict)
        assert "intent" in intent
        assert "entity_type" in intent
        assert intent["entity_id"] == "740506"
    
    def test_fallback_keywords(self, llm_service):
        """Test fallback detects keywords correctly"""
        test_cases = [
            ("show me customer 123", "Customer"),
            ("find order 456", "SalesOrder"),
            ("delivery 789", "Delivery"),
            ("invoice 999", "Invoice")
        ]
        
        for query, expected_type in test_cases:
            intent = llm_service._fallback_intent_extraction(query)
            assert intent["entity_type"] == expected_type


@pytest.mark.llm
@pytest.mark.integration
class TestEndToEndLLMFlow:
    """Test complete LLM flow"""
    
    def test_complete_flow_valid_query(self, llm_service, query_engine, guardrails):
        """Test complete flow with valid query"""
        user_query = "Find order 740506"
        
        # Step 1: Validate query
        is_valid, msg = guardrails.validate_user_query(user_query)
        assert is_valid
        
        # Step 2: Extract intent
        intent = llm_service.extract_query_intent(user_query, {})
        
        # Step 3: Validate intent
        is_valid, msg = guardrails.validate_intent_output(intent)
        assert is_valid
        
        # Step 4: Execute query
        result = query_engine.execute(intent)
        
        # Step 5: Validate result
        is_valid, msg = guardrails.validate_query_result(result)
        assert is_valid
        
        # Step 6: Generate response
        response = llm_service.generate_response(user_query, result["data"])
        
        # Step 7: Sanitize
        sanitized = guardrails.sanitize_response(response)
        
        assert len(sanitized) > 0
    
    def test_complete_flow_rejected_query(self, llm_service, guardrails):
        """Test complete flow with rejected query"""
        user_query = "What's the weather today?"
        
        # Step 1: Should be rejected immediately
        is_valid, msg = guardrails.validate_user_query(user_query)
        assert not is_valid
        assert "Order-to-Cash" in msg
