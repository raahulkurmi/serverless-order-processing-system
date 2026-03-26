# Serverless Order Processing System

A production-grade serverless backend built on AWS — API Gateway, SQS, Lambda, and DynamoDB.

![Architecture](architecture.png)

---

## Architecture

```
Client
  → API Gateway (auth + routing)
  → Lambda (input validation)
  → SQS (message queue)
  → Lambda (order processor)
  → DynamoDB (persistence)
        ↓
  orders-dlq (failed messages after 3 retries)
```

---

## Tech Stack

| Service | Role |
|---|---|
| API Gateway | REST API — receives HTTP requests, enforces API key auth |
| Lambda (Python 3.12) | Validates orders + processes SQS messages |
| SQS | Decouples API from processing, buffers messages |
| DynamoDB | Persists processed orders |
| IAM | Permissions between all services |

---

## Features

- Async order processing via SQS message queue
- Input validation — rejects bad requests before they touch the queue
- Idempotency — safe to retry, no duplicate orders saved
- Dead Letter Queue — failed messages parked after 3 retries
- GET endpoint — retrieve any order by ID
- API key authentication
- CORS enabled — works with browser frontend
- Batch processing — up to 10 messages per Lambda invocation
- Plain HTML + JS frontend — no framework needed

---

## Project Structure

```
serverless-order-processing/
│
├── README.md
├── architecture.png
│
├── lambda/
│   └── lambda_function.py        ← single Lambda handles all logic
│
├── frontend/
│   └── index.html                ← plain HTML frontend
│
└── docs/
    ├── setup.md                  ← manual AWS console setup steps
    └── api.md                    ← API reference
```

---

## API Reference

### POST /orders
Place a new order.

**Request headers:**
```
Content-Type: application/json
x-api-key: YOUR_API_KEY
```

**Request body:**
```json
{
  "order_id": "301",
  "item": "shoes",
  "qty": 2,
  "user_id": "user_123"
}
```

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
  "details": ["Missing required field: qty"]
}
```

---

### GET /orders/{order_id}
Retrieve an order by ID.

**Request headers:**
```
x-api-key: YOUR_API_KEY
```

**Response 200 — found:**
```json
{
  "order_id": "301",
  "item": "shoes",
  "qty": 2,
  "user_id": "user_123",
  "status": "processed",
  "created_at": "2026-03-26T09:39:12.666031+00:00"
}
```

**Response 404 — not found:**
```json
{
  "error": "Order 301 not found"
}
```

---

## Setup Guide

### Prerequisites
- AWS Account
- Python 3.12

---

### Step 1 — Create SQS Queue

1. AWS Console → SQS → Create queue
2. Type: **Standard**
3. Name: `orders-queue`
4. Visibility timeout: `30` seconds
5. Click **Create queue** — copy the Queue URL

---

### Step 2 — Create Dead Letter Queue

1. AWS Console → SQS → Create queue
2. Type: **Standard**
3. Name: `orders-dlq`
4. Click **Create queue** — copy the ARN

---

### Step 3 — Attach DLQ to main queue

1. SQS → `orders-queue` → Edit
2. Scroll to **Dead-letter queue** → Enable
3. Paste `orders-dlq` ARN
4. Maximum receives: `3`
5. Save

---

### Step 4 — Create DynamoDB Table

1. AWS Console → DynamoDB → Create table
2. Table name: `orders`
3. Partition key: `order_id` (String)
4. Leave all settings default → Create

---

### Step 5 — Create Lambda Function

1. AWS Console → Lambda → Create function
2. Author from scratch
3. Name: `order-processor`
4. Runtime: Python 3.12
5. Create function
6. Paste code from `lambda/lambda_function.py`
7. Update `QUEUE_URL` with your actual SQS queue URL
8. Click **Deploy**

---

### Step 6 — Attach IAM Permissions to Lambda

1. Lambda → Configuration → Permissions → click role name
2. Add permissions → Attach policies:
   - `AWSLambdaSQSQueueExecutionRole`
   - `AmazonSQSFullAccess`
   - `AmazonDynamoDBFullAccess`

---

### Step 7 — Connect SQS to Lambda

1. Lambda → Configuration → Triggers → Add trigger
2. Source: SQS
3. Queue: `orders-queue`
4. Batch size: `10`
5. Click **Add**

---

### Step 8 — Create API Gateway

1. AWS Console → API Gateway → Create API → REST API
2. Name: `orders-api`
3. Create resource: `/orders`
4. Create method: **POST** on `/orders`
   - Integration type: Lambda function
   - Enable Lambda proxy integration
   - Select `order-processor`
5. Create resource: `{order_id}` under `/orders`
6. Create method: **GET** on `/{order_id}`
   - Integration type: Lambda function
   - Enable Lambda proxy integration
   - Select `order-processor`
7. Enable CORS on both `/orders` and `/{order_id}`
8. Deploy API → stage name: `prod`

---

### Step 9 — Create IAM Role for API Gateway

1. IAM → Roles → Create role
2. Trusted entity: API Gateway
3. Name: `apigateway-sqs-role`
4. Attach policy: `AmazonSQSFullAccess`
5. Copy the role ARN

---

### Step 10 — Create API Key

1. API Gateway → API keys → Create API key
2. Name: `orders-api-key` → Save
3. API Gateway → Usage plans → Create
   - Name: `orders-plan`
   - Rate: 100/sec, Burst: 200, Quota: 10,000/month
4. Add API stage: `orders-api` → `prod`
5. Add API key: `orders-api-key`
6. Set API key required: `true` on POST and GET methods
7. Redeploy API → `prod`

---

### Step 11 — Run the Frontend

1. Open `frontend/index.html`
2. Update `API_URL` and `API_KEY` with your values
3. Open in browser — done

---

## Testing

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

**Test validation — missing fields:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"random": "garbage"}'
```

**Test validation — negative qty:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"order_id": "302", "item": "shoes", "qty": -1, "user_id": "user_123"}'
```

**Test without API key:**
```bash
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/orders/301
# Expected: {"message":"Forbidden"}
```

---

## Key Concepts

**Visibility timeout** — each Lambda retry gets a full fresh window. Three failures → message moves to DLQ.

**Idempotency** — before saving an order, Lambda checks if it already exists in DynamoDB. Duplicate messages are skipped safely.

**Dead Letter Queue** — messages that fail 3 times are moved to `orders-dlq` for manual inspection instead of retrying forever.

**Batch processing** — one Lambda invocation handles up to 10 messages. Fewer cold starts, cheaper, less database pressure.

**Decoupling** — API and processing are fully independent. The API returns success instantly. Processing happens asynchronously.

---

## Future Improvements

- [ ] SNS notifications on order completion
- [ ] Order status lifecycle: `pending → processing → completed`
- [ ] CloudWatch alarms when DLQ receives messages
- [ ] AWS Cognito for real user authentication
- [ ] Terraform / CDK for infrastructure as code

---

## License

MIT
