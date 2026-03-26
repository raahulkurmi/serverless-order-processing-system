# Serverless Order Processing System

A production-grade serverless backend built on AWS — API Gateway, SQS, Lambda, and DynamoDB.

<img width="709" height="439" alt="Screenshot 2026-03-26 at 11 49 29 PM" src="https://github.com/user-attachments/assets/99bde2b3-e769-4e24-8a94-d568afe0c13a" />


---

## Architecture

```
Client
  → API Gateway (auth + routing)
  → Lambda (validates → saves as pending → sends to SQS)
  → SQS (Lambda picks up → updates to processing)
  → Lambda (processes → updates to processed)
  → DynamoDB
        ↓
  orders-dlq → dlq-handler Lambda (updates to failed)
```

---

## Order Status Lifecycle

```
pending     → order received, saved to DB, sitting in queue
processing  → Lambda picked it up, currently being processed
processed   → successfully completed, saved to DynamoDB
failed      → failed 3 times, moved to DLQ, marked as failed
```

---

## Tech Stack

| Service | Role |
|---|---|
| API Gateway | REST API — receives HTTP requests, enforces API key auth |
| Lambda — order-processor | Validates orders + processes SQS messages |
| Lambda — dlq-handler | Marks failed orders in DynamoDB |
| SQS — orders-queue | Decouples API from processing, buffers messages |
| SQS — orders-dlq | Catches messages that fail 3 times |
| DynamoDB | Persists all orders with real-time status |
| IAM | Permissions between all services |

---

## Features

- Async order processing via SQS message queue
- Order status lifecycle: `pending → processing → processed → failed`
- Input validation — rejects bad requests before they touch the queue
- Idempotency — safe to retry, no duplicate orders saved
- Dead Letter Queue — failed messages parked after 3 retries
- DLQ handler Lambda — explicitly marks failed orders in DynamoDB
- GET endpoint — retrieve any order by ID with real-time status
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
├── .gitignore
├── .env.example
├── architecture.png
│
├── lambda/
│   ├── lambda_function.py      ← main Lambda — validates + processes orders
│   └── dlq_handler.py          ← DLQ Lambda — marks failed orders
│
├── frontend/
│   └── index.html              ← plain HTML frontend
│
└── docs/
    ├── setup.md                ← manual AWS console setup steps
    └── api.md                  ← API reference
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

Status values:
- `pending` — order received, waiting in queue
- `processing` — Lambda picked it up
- `processed` — successfully completed
- `failed` — failed 3 times, moved to DLQ

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

### Step 3 — Attach DLQ to Main Queue

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

### Step 5 — Create order-processor Lambda

1. AWS Console → Lambda → Create function
2. Name: `order-processor`
3. Runtime: Python 3.12
4. Paste code from `lambda/lambda_function.py`
5. Replace `YOUR_ACCOUNT_ID` in `QUEUE_URL`
6. Click **Deploy**

Attach these policies to its IAM role:
- `AWSLambdaSQSQueueExecutionRole`
- `AmazonSQSFullAccess`
- `AmazonDynamoDBFullAccess`

---

### Step 6 — Create dlq-handler Lambda

1. AWS Console → Lambda → Create function
2. Name: `dlq-handler`
3. Runtime: Python 3.12
4. Paste code from `lambda/dlq_handler.py`
5. Click **Deploy**

Attach these policies to its IAM role:
- `AWSLambdaSQSQueueExecutionRole`
- `AmazonDynamoDBFullAccess`

---

### Step 7 — Connect SQS Triggers

**order-processor:**
1. Lambda → `order-processor` → Configuration → Triggers → Add trigger
2. Source: SQS, Queue: `orders-queue`, Batch size: `10` → Add

**dlq-handler:**
1. Lambda → `dlq-handler` → Configuration → Triggers → Add trigger
2. Source: SQS, Queue: `orders-dlq`, Batch size: `10` → Add

---

### Step 8 — Create IAM Role for API Gateway

1. IAM → Roles → Create role
2. Trusted entity: API Gateway
3. Name: `apigateway-sqs-role`
4. Attach policy: `AmazonSQSFullAccess`
5. Copy the Role ARN

---

### Step 9 — Create API Gateway

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
7. Enable CORS on `/orders` — check POST
8. Enable CORS on `/{order_id}` — check GET
9. Deploy API → stage name: `prod`
10. Copy the Invoke URL

---

### Step 10 — Create API Key

1. API Gateway → API keys → Create API key
2. Name: `orders-api-key` → Save
3. API Gateway → Usage plans → Create
   - Name: `orders-plan`
   - Rate: `100` req/sec, Burst: `200`, Quota: `10000`/month
4. Add API stage: `orders-api` → `prod`
5. Add API key: `orders-api-key`
6. Set API key required: `true` on POST and GET methods
7. Redeploy API → `prod`
8. Copy the API key value

---

### Step 11 — Run the Frontend

1. Open `frontend/index.html`
2. Replace `YOUR_API_URL` with your Invoke URL
3. Replace `YOUR_API_KEY` with your API key value
4. Open in browser

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

---

## Key Concepts

**Order status lifecycle** — orders are saved immediately as `pending` so the frontend always has visibility. Status updates to `processing` when Lambda picks up, `processed` on success, `failed` if it hits the DLQ.

**Visibility timeout** — each Lambda retry gets a full fresh window. Three failures → message moves to DLQ.

**Idempotency** — before saving an order, Lambda checks if it already exists in DynamoDB. Duplicate messages are skipped safely.

**Dead Letter Queue** — messages that fail 3 times move to `orders-dlq`. The `dlq-handler` Lambda explicitly marks them as `failed` in DynamoDB.

**Batch processing** — one Lambda invocation handles up to 10 messages. Fewer cold starts, cheaper, less database pressure.

**Decoupling** — API and processing are fully independent. The API returns success instantly. Processing happens asynchronously.

**SQS vs Kafka** — SQS is a task queue: messages consumed and deleted. Kafka is an event log: messages stored, multiple consumers can read independently.

---

## Future Improvements

- [ ] SNS notifications on order completion
- [ ] CloudWatch alarms when DLQ receives messages
- [ ] AWS Cognito for real user authentication
- [ ] Terraform / CDK for infrastructure as code

---

## License

MIT
