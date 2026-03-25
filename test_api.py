"""
Test script for the API
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n[Test] Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_graph_stats():
    """Test graph statistics"""
    print("\n[Test] Graph Statistics")
    response = requests.get(f"{BASE_URL}/api/graph/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total Nodes: {data['total_nodes']}")
    print(f"Total Edges: {data['total_edges']}")
    return response.status_code == 200


def test_get_node():
    """Test get node"""
    print("\n[Test] Get Node - Order 740506")
    response = requests.post(
        f"{BASE_URL}/api/graph/node",
        json={"node_id": "SalesOrder:740506"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Order: {data.get('sales_order')}")
        print(f"Amount: {data.get('total_net_amount')} {data.get('transaction_currency')}")
    return response.status_code == 200


def test_order_flow():
    """Test order flow"""
    print("\n[Test] Order Flow - 740506")
    response = requests.post(
        f"{BASE_URL}/api/query/order-flow",
        json={"sales_order_id": "740506"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Items: {len(data.get('items', []))}")
        print(f"Deliveries: {len(data.get('deliveries', []))}")
        print(f"Invoices: {len(data.get('invoices', []))}")
        print(f"Payments: {len(data.get('payments', []))}")
    return response.status_code == 200


def test_search():
    """Test search"""
    print("\n[Test] Search - '740506'")
    response = requests.post(
        f"{BASE_URL}/api/graph/search",
        json={"query": "740506", "limit": 5}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('results', []))}")
    return response.status_code == 200


def test_chat():
    """Test chat endpoint"""
    print("\n[Test] Chat - 'Find order 740506'")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "Find order 740506"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data.get('response')[:200]}...")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def test_chat_journal_entry():
    """Test chat with journal entry query"""
    print("\n[Test] Chat - 'Find the journal entry for billing document 91150187'")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "91150187 - Find the journal entry number linked to this?"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data.get('response')}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("API Test Suite")
    print("="*60)
    
    tests = [
        ("Health Check", test_health),
        ("Graph Stats", test_graph_stats),
        ("Get Node", test_get_node),
        ("Order Flow", test_order_flow),
        ("Search", test_search),
        ("Chat - Basic", test_chat),
        ("Chat - Journal Entry", test_chat_journal_entry),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"Error: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nPassed: {passed_count}/{total_count}")


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Please ensure the server is running:")
        print("  python run_server.py")
