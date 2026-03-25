# Test Queries for Graph AI

## ✅ Queries to Test

### 1. Find Order
**Query:** `Find order 740506`

**Expected Response:**
- Should return order details
- Graph should highlight the order node
- Should show order flow with items, deliveries, invoices

---

### 2. Find Journal Entry (From Image 2)
**Query:** `91150187 - Find the journal entry number linked to this?`

**Expected Response:**
- Should find billing document 91150187
- Should locate linked journal entry
- Should return the journal entry number: **9400635958**

---

### 3. Trace Order Flow
**Query:** `Trace the flow of order 740506`

**Expected Response:**
- Complete order-to-cash flow
- Shows: Order → Items → Deliveries → Invoices → Payments
- Highlights all connected nodes in graph

---

### 4. Customer Analytics
**Query:** `Show me customer 310000108`

**Expected Response:**
- Customer details
- Total orders
- Order value
- Payment information

---

### 5. Search Query
**Query:** `Find deliveries`

**Expected Response:**
- List of delivery documents
- Multiple results
- Should be searchable

---

## ❌ Queries that Should Be Rejected

### 1. Out of Scope
**Query:** `What's the weather today?`

**Expected:** Should be rejected with message about O2C scope only

---

### 2. Malicious Query
**Query:** `SELECT * FROM users WHERE 1=1`

**Expected:** Should be blocked by guardrails

---

## 🎯 How to Test

1. Open http://localhost:3000
2. Type each query in the chat
3. Verify the response matches expected
4. Check graph highlights relevant nodes
5. Verify node details panel shows correct info

---

## 📊 Graph Visualization Checks

- ✅ Nodes spread naturally (force-directed layout)
- ✅ Clusters visible (related nodes grouped)
- ✅ Edges connect properly
- ✅ Highlighted nodes visible when query runs
- ✅ Can click nodes to see details
- ✅ Can drag nodes around
- ✅ Minimap shows overview

---

## 🔧 If Issues Occur

1. **Graph not showing:** Refresh page
2. **AI not responding:** Check backend logs
3. **Wrong answer:** Check query engine logic
4. **Nodes overlapping:** Layout will settle after load
5. **Can't click nodes:** Make sure graph is loaded

---

## ✅ Success Criteria

- [x] Graph renders in force-directed layout
- [x] Nodes cluster naturally
- [x] AI answers questions correctly
- [x] Journal entry query works (like in image 2)
- [x] Order flow traces properly
- [x] Graph highlights relevant nodes
- [x] UI is responsive and clean
