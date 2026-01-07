# Real-time & Supplier APIs

This file documents the new lightweight real-time and supplier endpoints added to VendorConnect.

## Endpoints

- GET /api/supplier/orders
  - Returns JSON list of orders for the logged-in supplier (requires `supplier_id` in session).

- POST /api/supplier/orders/<order_id>/action
  - Body: { "action": "accept" | "reject" | "mark_preparing" | "mark_ready" | "out_for_delivery" | "delivered" }
  - Returns: { success: true, status: "confirmed" }
  - Publishes a `status_update` event for the order and supplier queues.

- GET /api/supplier/events
  - Server-Sent Events (SSE). Supplier dashboard clients may open EventSource to this endpoint to receive real-time events for all orders of the logged-in supplier.

- GET /api/order/<order_id>/events
  - SSE endpoint for a single order (vendor/supplier scopes) to receive order-specific events.

- GET /api/customer/order/<order_id>/events
  - SSE endpoint for customers to receive order status and location updates for their order.

- GET /api/order/<order_id>/tracking
  - Returns the current order object and items for display in trackers.

## Notes & recommendations

- Current implementation uses in-memory queues and is suitable for local development and demos. For production, use an external pub/sub (Redis, RabbitMQ, etc.) so multiple worker processes and instances can share events.
- SSE connections are simple to use with `new EventSource('/api/supplier/events')`. The server sends JSON-encoded event payloads under the `data:` field.

Example payload:

{
  "type": "status_update",
  "data": { "order_id": 123, "status": "out_for_delivery" },
  "timestamp": "2026-01-07T12:34:56.789"
}

