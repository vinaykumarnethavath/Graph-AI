import axios from 'axios'

const BASE_URL = ''

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Graph endpoints
  getGraphStats: async () => {
    const { data } = await client.get('/api/graph/stats')
    return data
  },

  getFullGraph: async () => {
    const { data } = await client.get('/api/graph/full')
    return data
  },

  getNode: async (nodeId) => {
    const { data } = await client.post('/api/graph/node', { node_id: nodeId })
    return data
  },

  getSubgraph: async (nodeId, depth = 2) => {
    const { data } = await client.post('/api/graph/subgraph', {
      node_id: nodeId,
      depth: depth,
    })
    return data
  },

  searchNodes: async (query, entityTypes = null, limit = 20) => {
    const { data } = await client.post('/api/graph/search', {
      query,
      entity_types: entityTypes,
      limit,
    })
    return data.results
  },

  // Query endpoints
  getOrderFlow: async (salesOrderId) => {
    const { data } = await client.post('/api/query/order-flow', {
      sales_order_id: salesOrderId,
    })
    return data
  },

  getCustomerAnalytics: async (customerId) => {
    const { data } = await client.post('/api/query/customer-analytics', {
      customer_id: customerId,
    })
    return data
  },

  traceDocumentFlow: async (documentId, documentType) => {
    const { data } = await client.post('/api/query/document-flow', {
      document_id: documentId,
      document_type: documentType,
    })
    return data
  },

  // Chat endpoint
  chat: async (message, sessionId = null) => {
    const { data } = await client.post('/api/chat', {
      message,
      session_id: sessionId,
    })
    return data
  },

  clearChat: async () => {
    const { data } = await client.post('/api/chat/clear')
    return data
  },
}

export default client
