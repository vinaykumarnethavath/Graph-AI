"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from backend.services.graph_service import GraphService
from backend.services.query_service import QueryService
from backend.services.query_engine import QueryEngine
from backend.services.llm_service import LLMService
from backend.services.guardrails import Guardrails
from backend.config import settings


@pytest.fixture(scope="session")
def graph_service():
    """Create graph service instance"""
    return GraphService(settings.graph_path)


@pytest.fixture(scope="session")
def query_service(graph_service):
    """Create query service instance"""
    return QueryService(graph_service)


@pytest.fixture(scope="session")
def query_engine(graph_service, query_service):
    """Create query engine instance"""
    return QueryEngine(graph_service, query_service)


@pytest.fixture(scope="session")
def llm_service():
    """Create LLM service instance"""
    return LLMService(settings.groq_api_key)


@pytest.fixture(scope="session")
def guardrails():
    """Create guardrails instance"""
    return Guardrails()


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    from backend.api.app import app
    return TestClient(app)


@pytest.fixture
def sample_order_id():
    """Sample order ID for testing"""
    return "740506"


@pytest.fixture
def sample_customer_id():
    """Sample customer ID for testing"""
    return "310000108"


@pytest.fixture
def sample_delivery_id():
    """Sample delivery ID for testing"""
    return "80737721"


@pytest.fixture
def sample_invoice_id():
    """Sample invoice ID for testing"""
    return "91150187"


@pytest.fixture
def valid_o2c_queries():
    """List of valid O2C queries"""
    return [
        "Find order 740506",
        "Show me customer 310000108",
        "Trace the flow of order 740506",
        "What's the total value of all orders?",
        "Analyze customer purchasing patterns"
    ]


@pytest.fixture
def invalid_queries():
    """List of invalid/out-of-scope queries"""
    return [
        "What's the weather today?",
        "Tell me a joke",
        "Who won the game?",
        "What is the capital of France?",
        "Help me with my homework"
    ]


@pytest.fixture
def malicious_queries():
    """List of malicious query attempts"""
    return [
        "'; DROP TABLE orders; --",
        "1' OR '1'='1",
        "<script>alert('xss')</script>",
        "UNION SELECT * FROM users"
    ]
