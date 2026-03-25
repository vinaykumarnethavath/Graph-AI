# Testing Guide

## Overview

Comprehensive pytest test suite covering API endpoints, query correctness, edge cases, and LLM validation.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Fixtures and configuration
├── test_api.py              # FastAPI endpoint tests
├── test_query_engine.py     # Query correctness tests
├── test_edge_cases.py       # Edge case handling tests
└── test_llm_validation.py   # LLM output validation tests
```

## Quick Start

### Install Dependencies

```bash
pip install pytest pytest-cov httpx
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# API tests only
pytest tests/ -m api -v

# Query tests only
pytest tests/ -m query -v

# Edge case tests only
pytest tests/ -m edge -v

# LLM tests only (slower)
pytest tests/ -m llm -v

# Fast tests (exclude slow LLM tests)
pytest tests/ -m "not slow" -v
```

### Using Test Runner Script

```bash
# Run all tests
python run_tests.py all

# Run specific category
python run_tests.py api
python run_tests.py query
python run_tests.py edge
python run_tests.py llm

# Run fast tests only
python run_tests.py fast

# Run with coverage report
python run_tests.py coverage
```

## Test Categories

### 1. API Tests (`test_api.py`)

**Tests:** 20+ endpoints

✅ Health check  
✅ Graph statistics  
✅ Node retrieval  
✅ Search functionality  
✅ Subgraph extraction  
✅ Order flow  
✅ Customer analytics  
✅ Chat endpoint  
✅ Error handling  

**Example:**
```python
def test_get_node_valid(api_client, sample_order_id):
    response = api_client.post("/api/graph/node", json={
        "node_id": f"SalesOrder:{sample_order_id}"
    })
    assert response.status_code == 200
```

### 2. Query Tests (`test_query_engine.py`)

**Tests:** Query correctness and execution

✅ Get details  
✅ Search  
✅ Flow tracing  
✅ Aggregations (count, sum, avg, group_by)  
✅ Missing link detection  
✅ Customer analytics  
✅ Execution metadata  

**Example:**
```python
def test_trace_flow_valid_order(query_engine, sample_order_id):
    query = {
        "intent": "trace_flow",
        "entity_type": "SalesOrder",
        "entity_id": sample_order_id
    }
    result = query_engine.execute(query)
    assert result["success"] is True
```

### 3. Edge Case Tests (`test_edge_cases.py`)

**Tests:** Error handling and boundary conditions

✅ Invalid inputs  
✅ Null and empty values  
✅ Boundary conditions  
✅ Duplicate data  
✅ Circular references  
✅ Special characters  
✅ Concurrent operations  
✅ Error recovery  

**Example:**
```python
def test_search_empty_results(query_engine):
    query = {
        "intent": "search",
        "entity_id": "NONEXISTENT_999"
    }
    result = query_engine.execute(query)
    assert result["success"] is True
    assert len(result["data"]) == 0
```

### 4. LLM Validation Tests (`test_llm_validation.py`)

**Tests:** LLM integration and guardrails

✅ Intent extraction  
✅ Query validation  
✅ Malicious query blocking  
✅ Intent structure validation  
✅ Entity type validation  
✅ Response sanitization  
✅ Fallback mechanisms  
✅ End-to-end flow  

**Example:**
```python
def test_validate_malicious_queries(guardrails, malicious_queries):
    for query in malicious_queries:
        is_valid, msg = guardrails.validate_user_query(query)
        assert not is_valid
```

## Fixtures

### Service Fixtures (Session Scoped)

```python
@pytest.fixture(scope="session")
def graph_service():
    """Shared graph service"""
    return GraphService("processed_data/graph.gpickle")

@pytest.fixture(scope="session")
def query_engine(graph_service, query_service):
    """Shared query engine"""
    return QueryEngine(graph_service, query_service)
```

### Data Fixtures

```python
@pytest.fixture
def sample_order_id():
    return "740506"

@pytest.fixture
def valid_o2c_queries():
    return [
        "Find order 740506",
        "Show me customer 310000108",
        # ...
    ]
```

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_api.py -v
```

### Specific Test Class

```bash
pytest tests/test_api.py::TestChatEndpoint -v
```

### Specific Test Function

```bash
pytest tests/test_api.py::TestChatEndpoint::test_chat_valid_query -v
```

### With Output

```bash
pytest tests/ -v -s  # -s shows print statements
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Run Last Failed Tests

```bash
pytest tests/ --lf
```

## Coverage Report

### Generate HTML Coverage Report

```bash
pytest tests/ --cov=services --cov=api --cov-report=html
```

View report: `htmlcov/index.html`

### Terminal Coverage Report

```bash
pytest tests/ --cov=services --cov=api --cov-report=term
```

### Coverage by Module

```bash
pytest tests/ --cov=services.query_engine --cov-report=term
```

## Test Markers

### Built-in Markers

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.query` - Query engine tests
- `@pytest.mark.edge` - Edge case tests
- `@pytest.mark.llm` - LLM integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.integration` - Integration tests

### Run by Marker

```bash
pytest tests/ -m api
pytest tests/ -m query
pytest tests/ -m "not slow"
pytest tests/ -m "api and not slow"
```

## Test Statistics

### Current Test Count

- **API Tests**: 20+ tests
- **Query Tests**: 15+ tests
- **Edge Case Tests**: 15+ tests
- **LLM Tests**: 15+ tests
- **Total**: 65+ tests

### Expected Run Times

- Fast tests (no LLM): ~5-10 seconds
- All tests (with LLM): ~30-60 seconds
- Coverage report: +5-10 seconds

## Debugging Failed Tests

### Verbose Output

```bash
pytest tests/test_api.py::test_name -vv
```

### Show Locals on Failure

```bash
pytest tests/ -l
```

### Drop into Debugger on Failure

```bash
pytest tests/ --pdb
```

### Print Statements

```bash
pytest tests/ -s
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov
```

## Best Practices

✅ **Run tests before commits**  
✅ **Keep tests fast** (mock expensive operations)  
✅ **Test one thing per test**  
✅ **Use descriptive test names**  
✅ **Use fixtures for setup**  
✅ **Test edge cases**  
✅ **Maintain high coverage** (aim for >80%)  

## Common Issues

### Issue: Tests fail due to missing graph file

**Solution:**
```bash
python build_graph.py  # Build graph first
```

### Issue: LLM tests fail

**Solution:** Check `.env` has valid `GROQ_API_KEY`

### Issue: Import errors

**Solution:**
```bash
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Slow tests

**Solution:** Run fast tests only:
```bash
pytest tests/ -m "not slow"
```

## Writing New Tests

### Template

```python
@pytest.mark.your_marker
class TestYourFeature:
    """Test your feature"""
    
    def test_basic_case(self, fixture):
        """Test basic functionality"""
        # Arrange
        input_data = "test"
        
        # Act
        result = some_function(input_data)
        
        # Assert
        assert result == expected
    
    def test_edge_case(self, fixture):
        """Test edge case"""
        # Test boundary condition
        pass
    
    def test_error_handling(self, fixture):
        """Test error handling"""
        with pytest.raises(SomeException):
            some_function(invalid_input)
```

## Test Output

### Successful Run

```
======================== test session starts ========================
collected 65 items

tests/test_api.py::TestHealthEndpoint::test_health_check PASSED
tests/test_api.py::TestGraphEndpoints::test_get_graph_stats PASSED
...
==================== 65 passed in 45.2s ====================
```

### Failed Test

```
FAILED tests/test_api.py::TestChatEndpoint::test_chat_valid_query
________________________ TestChatEndpoint.test_chat_valid_query ________________________
...
AssertionError: assert False
```

## Summary

✅ **65+ comprehensive tests**  
✅ **API, query, edge case, and LLM coverage**  
✅ **Fixtures for reusable test data**  
✅ **Markers for selective test runs**  
✅ **Coverage reporting**  
✅ **Easy to extend**  

**Run tests regularly to ensure code quality!**
