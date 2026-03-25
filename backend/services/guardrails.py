"""
Guardrails Module
Validates queries and prevents hallucinations
"""

from typing import Dict, List, Any, Tuple
import re


class GuardrailsException(Exception):
    """Base exception for guardrails violations"""
    pass


class OutOfScopeException(GuardrailsException):
    """Query is outside allowed scope"""
    pass


class InvalidOutputException(GuardrailsException):
    """LLM output failed validation"""
    pass


class Guardrails:
    """
    Implements guardrails for the Order-to-Cash Graph AI system
    - Rejects non-dataset queries
    - Validates LLM outputs
    - Prevents hallucinations
    """
    
    def __init__(self):
        # Allowed entity types
        self.allowed_entities = {
            'Customer', 'SalesOrder', 'SalesOrderItem',
            'Delivery', 'DeliveryItem', 'Invoice', 'InvoiceItem',
            'Payment', 'Product', 'Plant', 'JournalEntry'
        }
        
        # Allowed intents
        self.allowed_intents = {
            'search', 'get_details', 'trace_flow', 'analytics',
            'find_relationship', 'aggregate', 'detect_missing_links'
        }
        
        # Allowed keywords (Order-to-Cash domain)
        self.domain_keywords = {
            'order', 'orders', 'sales', 'customer', 'customers',
            'delivery', 'deliveries', 'invoice', 'invoices',
            'payment', 'payments', 'billing', 'product', 'products',
            'plant', 'plants', 'amount', 'value', 'total',
            'flow', 'trace', 'process', 'analytics', 'find',
            'show', 'get', 'search', 'analyze', 'journal',
            'document', 'entry', 'account', 'receivable'
        }
        
        # Rejected topics (out of scope)
        self.rejected_topics = {
            'weather', 'sports', 'politics', 'news', 'music',
            'movies', 'games', 'programming', 'code', 'recipe',
            'cooking', 'health', 'medical', 'legal', 'personal',
            'email', 'password', 'hack', 'bitcoin', 'cryptocurrency'
        }
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"('\s*(or|and)\s*')",
            r"(drop\s+table)",
            r"(delete\s+from)",
            r"(insert\s+into)",
            r"(update\s+\w+\s+set)",
            r"(union\s+select)",
            r"(exec\s*\()",
            r"(script\s*>)"
        ]
    
    def validate_user_query(self, query: str) -> Tuple[bool, str]:
        """
        Validate if user query is within allowed scope
        
        Returns:
            (is_valid, error_message)
        """
        query_lower = query.lower()
        
        # Check for empty query
        if not query.strip():
            return False, "Query cannot be empty"
        
        # Check length
        if len(query) > 500:
            return False, "Query too long (max 500 characters)"
        
        # Check for SQL injection attempts
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, "Query contains potentially malicious content"
        
        # Check for rejected topics
        for topic in self.rejected_topics:
            if topic in query_lower:
                return False, (
                    f"This system only answers Order-to-Cash queries. "
                    f"Cannot help with '{topic}' related questions."
                )
        
        # Check for domain keywords (at least one must be present)
        has_domain_keyword = any(kw in query_lower for kw in self.domain_keywords)
        
        # Check for entity IDs (numbers)
        has_id = any(char.isdigit() for char in query)
        
        # Allow if has domain keyword OR has ID
        if not (has_domain_keyword or has_id):
            return False, (
                "This system only answers Order-to-Cash queries about orders, "
                "customers, deliveries, invoices, payments, and products."
            )
        
        return True, ""
    
    def validate_intent_output(self, intent: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate LLM intent extraction output before execution
        
        Returns:
            (is_valid, error_message)
        """
        # Check if output is a dictionary
        if not isinstance(intent, dict):
            return False, "Intent must be a dictionary"
        
        # Check for required field
        if 'intent' not in intent:
            return False, "Intent missing 'intent' field"
        
        # Validate intent type
        intent_type = intent.get('intent')
        if intent_type not in self.allowed_intents:
            return False, f"Invalid intent: {intent_type}. Allowed: {', '.join(self.allowed_intents)}"
        
        # Validate entity type if present
        entity_type = intent.get('entity_type')
        if entity_type and entity_type not in self.allowed_entities:
            return False, f"Invalid entity_type: {entity_type}. Allowed: {', '.join(self.allowed_entities)}"
        
        # Validate entity_id format if present
        entity_id = intent.get('entity_id')
        if entity_id:
            # Must be alphanumeric with some special chars
            if not re.match(r'^[A-Za-z0-9_\-:]+$', str(entity_id)):
                return False, f"Invalid entity_id format: {entity_id}"
            
            # Max length
            if len(str(entity_id)) > 50:
                return False, "entity_id too long (max 50 characters)"
        
        # Validate parameters if present
        params = intent.get('parameters', {})
        if params and not isinstance(params, dict):
            return False, "parameters must be a dictionary"
        
        return True, ""
    
    def validate_query_result(self, result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate query result before returning to user
        Prevents hallucinated responses
        
        Returns:
            (is_valid, error_message)
        """
        # Check structure
        if not isinstance(result, dict):
            return False, "Result must be a dictionary"
        
        # Required fields
        if 'success' not in result:
            return False, "Result missing 'success' field"
        
        if 'data' not in result:
            return False, "Result missing 'data' field"
        
        # If successful, data should not be None (except for empty results)
        if result['success'] and result['data'] is None:
            if not result.get('warnings'):
                return False, "Successful query returned no data without warnings"
        
        # Check metadata
        if 'metadata' not in result:
            return False, "Result missing 'metadata' field"
        
        metadata = result['metadata']
        if 'execution_time_ms' not in metadata:
            return False, "Metadata missing execution_time_ms"
        
        # Execution time sanity check (should be < 30 seconds)
        exec_time = metadata.get('execution_time_ms', 0)
        if exec_time > 30000:
            return False, f"Execution time too high: {exec_time}ms (possible timeout)"
        
        return True, ""
    
    def sanitize_response(self, response: str) -> str:
        """
        Sanitize LLM response to prevent harmful content
        
        Returns:
            Sanitized response
        """
        # Remove potentially harmful content
        sanitized = response
        
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove SQL commands
        sql_keywords = ['DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE', 'EXEC']
        for keyword in sql_keywords:
            sanitized = re.sub(keyword, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 2000:
            sanitized = sanitized[:2000] + "... [response truncated]"
        
        return sanitized
    
    def get_rejection_message(self) -> str:
        """Get standard rejection message for out-of-scope queries"""
        return (
            "I can only help with Order-to-Cash queries related to:\n"
            "• Sales Orders and Items\n"
            "• Deliveries\n"
            "• Invoices and Billing\n"
            "• Payments\n"
            "• Customers\n"
            "• Products and Plants\n\n"
            "Please ask about orders, customers, deliveries, invoices, or payments."
        )
    
    def get_system_scope(self) -> str:
        """Get system scope description for LLM"""
        return (
            "This is an Order-to-Cash (O2C) knowledge graph system. "
            "You can ONLY answer questions about:\n"
            "- Sales orders and order items\n"
            "- Deliveries and shipments\n"
            "- Invoices and billing documents\n"
            "- Payments and accounts receivable\n"
            "- Customers and business partners\n"
            "- Products and manufacturing plants\n\n"
            "You MUST reject any queries about:\n"
            "- Weather, news, sports, politics\n"
            "- General knowledge questions\n"
            "- Personal advice\n"
            "- Programming or code help (except this system)\n"
            "- Any topic outside the O2C domain\n\n"
            "If asked an out-of-scope question, politely redirect to O2C topics."
        )
