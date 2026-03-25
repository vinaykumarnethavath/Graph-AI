"""
LLM Service Layer
Handles Groq API integration for natural language understanding
"""

from groq import Groq
from typing import Dict, List, Any, Optional
import json


class LLMService:
    """Service for LLM-powered graph queries using Groq API"""
    
    MAX_HISTORY_PER_SESSION = 10  # Limit history size
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.sessions = {}  # session_id -> conversation_history
    
    def _get_session_history(self, session_id: Optional[str] = None) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id is None:
            session_id = "default"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        return self.sessions[session_id]
    
    def _add_to_history(self, session_id: Optional[str], role: str, content: str):
        """Add message to session history with size limit"""
        history = self._get_session_history(session_id)
        history.append({"role": role, "content": content})
        
        # Keep only last MAX_HISTORY_PER_SESSION messages
        if len(history) > self.MAX_HISTORY_PER_SESSION:
            self.sessions[session_id or "default"] = history[-self.MAX_HISTORY_PER_SESSION:]
    
    def extract_query_intent(self, user_query: str, graph_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured intent from natural language query"""
        
        system_prompt = f"""You are a STRICT graph query assistant for an Order-to-Cash knowledge graph.

CRITICAL RULES:
1. You can ONLY process queries about Order-to-Cash business processes
2. REJECT any queries about: weather, sports, news, politics, personal advice, general knowledge
3. You must ONLY return valid JSON with the specified structure
4. Do NOT make up entity IDs or data
5. Do NOT answer questions outside the O2C domain

ALLOWED TOPICS ONLY:
- Sales orders, deliveries, invoices, payments
- Customers, products, plants
- Order-to-cash flow and analytics

If the query is out of scope, return:
{{"intent": "out_of_scope", "entity_type": null, "entity_id": null, "parameters": {{}}, "question_type": "invalid"}}


Available entities:
- Customer: Business partners
- SalesOrder: Sales orders
- SalesOrderItem: Order line items
- Delivery: Outbound deliveries
- Invoice: Billing documents
- Payment: Payment transactions
- Product: Materials/products
- Plant: Manufacturing facilities

Graph statistics:
{json.dumps(graph_stats, indent=2)}

Extract the user's intent and return a JSON object with:
- intent: The type of query (search, trace_flow, analytics, find_relationship, get_details)
- entity_type: The main entity type being queried
- entity_id: Specific ID if mentioned
- parameters: Additional query parameters
- question_type: The type of question (what, how, why, find, analyze)

Examples:
User: "Find order 740506"
{{"intent": "get_details", "entity_type": "SalesOrder", "entity_id": "740506", "parameters": {{}}, "question_type": "find"}}

User: "Show me customer 310000108"
{{"intent": "get_details", "entity_type": "Customer", "entity_id": "310000108", "parameters": {{}}, "question_type": "find"}}

User: "Trace the flow of order 740506"
{{"intent": "trace_flow", "entity_type": "SalesOrder", "entity_id": "740506", "parameters": {{}}, "question_type": "how"}}

User: "Find the journal entry for billing document 91150187"
{{"intent": "find_relationship", "entity_type": "Invoice", "entity_id": "91150187", "parameters": {{"target": "JournalEntry"}}, "question_type": "find"}}

User: "How many orders did each customer place?"
{{"intent": "aggregate", "entity_type": "SalesOrder", "entity_id": null, "parameters": {{"aggregation": "group_by", "field": "customer"}}, "question_type": "analyze"}}

User: "Number of orders each customer placed"
{{"intent": "aggregate", "entity_type": "SalesOrder", "entity_id": null, "parameters": {{"aggregation": "group_by", "field": "customer"}}, "question_type": "analyze"}}

Return ONLY valid JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            intent = json.loads(content)
            return intent
            
        except Exception as e:
            # Fallback to simple keyword extraction
            return self._fallback_intent_extraction(user_query)
    
    def _fallback_intent_extraction(self, query: str) -> Dict[str, Any]:
        """Fallback intent extraction using keywords"""
        query_lower = query.lower()
        
        intent = {
            'intent': 'search',
            'entity_type': None,
            'entity_id': None,
            'parameters': {},
            'question_type': 'find'
        }
        
        # Detect entity type
        if 'order' in query_lower:
            intent['entity_type'] = 'SalesOrder'
        elif 'customer' in query_lower:
            intent['entity_type'] = 'Customer'
        elif 'invoice' in query_lower or 'billing' in query_lower:
            intent['entity_type'] = 'Invoice'
        elif 'delivery' in query_lower:
            intent['entity_type'] = 'Delivery'
        elif 'payment' in query_lower:
            intent['entity_type'] = 'Payment'
        elif 'product' in query_lower:
            intent['entity_type'] = 'Product'

        if ('each customer' in query_lower or 'per customer' in query_lower) and 'order' in query_lower:
            intent['intent'] = 'aggregate'
            intent['entity_type'] = 'SalesOrder'
            intent['parameters'] = {
                'aggregation': 'group_by',
                'field': 'customer'
            }
            intent['question_type'] = 'analyze'
            return intent

        if ('how many' in query_lower or 'number of' in query_lower or 'count' in query_lower):
            intent['intent'] = 'aggregate'
            intent['question_type'] = 'analyze'
            intent['parameters'] = {
                'aggregation': 'count'
            }
        
        # Detect intent, session_id: Optional[str] = None
        if 'trace' in query_lower or 'flow' in query_lower:
            intent['intent'] = 'trace_flow'
            intent['question_type'] = 'how'
        elif 'analyz' in query_lower or 'statistic' in query_lower:
            intent['intent'] = 'analytics'
            intent['question_type'] = 'analyze'
        elif 'find' in query_lower or 'show' in query_lower or 'get' in query_lower:
            intent['intent'] = 'get_details'
        
        # Try to extract ID (simple number extraction)
        words = query.split()
        for word in words:
            if word.isdigit():
                intent['entity_id'] = word
                break
        
        return intent
    
    def generate_response(self, query: str, query_result: Any, context: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Generate natural language response from query results"""
        
        system_prompt = """You are Graph AI, a STRICT Order-to-Cash graph assistant.

CRITICAL RULES:
1. ONLY discuss Order-to-Cash topics (orders, deliveries, invoices, payments, customers, products)
2. NEVER make up or hallucinate data - use ONLY what's in the query results
3. If data is missing or null, explicitly state "not available" or "no data found"
4. Do NOT answer questions outside the O2C domain
5. Do NOT provide personal opinions or general advice

Your role:
- Analyze graph query results ONLY
- Provide clear, factual answers based on actual data
- State clearly when information is missing
- Suggest O2C-related follow-up questions only

Guidelines:
- Be conversational but strictly factual
- Format numbers with proper currency and units
- Explain relationships using actual graph data
- Never infer or guess missing information
- Keep responses focused on O2C domain"""

        # Format query result for LLM
        result_text = json.dumps(query_result, indent=2, default=str) if query_result else "No results found"
        
        user_message = f"""User query: {query}

Query results:
{result_text}

{f"Additional context: {context}" if context else ""}

Please provide a helpful response to the user's query based on these results."""

        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 4 messages)
            history = self._get_session_history(session_id)
            if history:
                messages.extend(history[-4:])
            
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # Update conversation history
            self._add_to_history(session_id, "user", query)
            self._add_to_history(session_id, "assistant", answer)
            
            return answer
            
        except Exception as e:
            return f"I found the requested information, but encountered an error generating the response: {str(e)}"
    
    def chat(self, message: str, graph_context: Optional[Dict] = None, session_id: Optional[str] = None) -> str:
        """General chat interface"""
        
        system_prompt = """You are Graph AI, a STRICT Order-to-Cash knowledge graph assistant.

SCOPE LIMITATION:
You can ONLY help with Order-to-Cash topics:
- Find orders, deliveries, invoices, and payments
- Trace document flows through the O2C process
- Analyze customer behavior and patterns
- Search for specific entities
- Answer questions about the graph structure

YOU MUST REJECT queries about:
- Weather, news, sports, entertainment
- General knowledge or trivia
- Personal advice or opinions
- Programming help (except this system)
- Any topic outside Order-to-Cash domain

If asked an out-of-scope question, politely respond:
"I can only help with Order-to-Cash queries about orders, customers, deliveries, invoices, and payments. Please ask about these topics."

Be helpful within the O2C domain, but strictly reject everything else."""

        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if graph_context:
                context_msg = f"Graph context: {json.dumps(graph_context, default=str)}"
                messages.append({"role": "system", "content": context_msg})
            
            # Add history
            history = self._get_session_history(session_id)
            if history:
                messages.extend(history[-6:])
            
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            
            # Update history
            self._add_to_history(session_id, "user", message)
            self._add_to_history(session_id, "assistant", answer)
            
            return answer
            
        except Exception as e:
            return f"I encountered an error: {str(e)}"
    
    def clear_history(self, session_id: Optional[str] = None):
        """Clear conversation history for a session"""
        if session_id is None:
            session_id = "default"
        
        if session_id in self.sessions:
            self.sessions[session_id] = []
        
        # Also clear old sessions (memory management)
        if len(self.sessions) > 100:  # Keep max 100 sessions
            # Remove oldest sessions
            sorted_sessions = sorted(self.sessions.items(), key=lambda x: len(x[1]))
            self.sessions = dict(sorted_sessions[-50:])
