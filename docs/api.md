# API Reference

Base URL:
```
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
```

All requests require the API key header:
```
x-api-key: YOUR_API_KEY
```

---

## POST /orders

Place a new order.

**Request body:**
```json
{
  "order_id": "301",
  "item": "shoes",
  "qty": 2,
  "user_id": "user_123"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| order_id | string | yes | unique identifier |
| item | string | yes | item name |
| qty | number | yes | must be greater than 0 |
| user_id | string | yes | user identifier |

**Response 202 — accepted:**
```json
{
  "message": "Order accepted",
  "order_id": "301"
}
```

**Response 400 — validation failed:**
```json
{
  "error": "Validation failed",
  "details": [
    "Missing required field: qty",
    "item cannot be empty"
  ]
}
```

**Response 403 — missing or invalid API key:**
```json
{
  "message": "Forbidden"
}
```

---

## GET /orders/{order_id}

Retrieve an order by ID.

**Example:**
```
GET /orders/301
```

**Response 200 — found:**
```json
{
  "order_id": "301",
  "item": "shoes",
  "qty": 2,
  "user_id": "user_123",
  "status": "processed",
  "message_id": "abc123-...",
  "created_at": "2026-03-26T09:39:12.666031+00:00"
}
```

**Response 404 — not found:**
```json
{
  "error": "Order 301 not found"
}
```

**Response 403 — missing or invalid API key:**
```json
{
  "message": "Forbidden"
}
```

---

## Example curl commands

**Place an order:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"order_id": "301", "item": "shoes", "qty": 2, "user_id": "user_123"}'
```

**Get an order:**
```bash
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/301 \
  -H "x-api-key: YOUR_API_KEY"
```

**Test validation:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"random": "garbage"}'
```

**Test without API key:**
```bash
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/301
```
