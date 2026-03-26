# Setup Guide

Complete step-by-step instructions to deploy this project on AWS.

## Prerequisites
- AWS Account
- Python 3.12

---

## Step 1 — Create SQS Queue

1. AWS Console → SQS → Create queue
2. Type: **Standard**
3. Name: `orders-queue`
4. Visibility timeout: `30` seconds
5. Click **Create queue**
6. Copy the **Queue URL** — you'll need it in Lambda

---

## Step 2 — Create Dead Letter Queue

1. AWS Console → SQS → Create queue
2. Type: **Standard**
3. Name: `orders-dlq`
4. Click **Create queue**
5. Copy the **ARN**

---

## Step 3 — Attach DLQ to Main Queue

1. SQS → `orders-queue` → Edit
2. Scroll to **Dead-letter queue** section → Enable
3. Paste `orders-dlq` ARN
4. Maximum receives: `3`
5. Save

---

## Step 4 — Create DynamoDB Table

1. AWS Console → DynamoDB → Create table
2. Table name: `orders`
3. Partition key: `order_id` (String)
4. Leave all settings default → Create table

---

## Step 5 — Create Lambda Function

1. AWS Console → Lambda → Create function
2. Author from scratch
3. Name: `order-processor`
4. Runtime: Python 3.12
5. Create function
6. Paste code from `lambda/lambda_function.py`
7. Replace `YOUR_ACCOUNT_ID` in `QUEUE_URL` with your actual AWS account ID
8. Click **Deploy**

---

## Step 6 — Attach IAM Permissions to Lambda

1. Lambda → Configuration → Permissions → click the role name
2. Add permissions → Attach policies:
   - `AWSLambdaSQSQueueExecutionRole`
   - `AmazonSQSFullAccess`
   - `AmazonDynamoDBFullAccess`

---

## Step 7 — Connect SQS to Lambda

1. Lambda → Configuration → Triggers → Add trigger
2. Source: SQS
3. Queue: `orders-queue`
4. Batch size: `10`
5. Click **Add**

---

## Step 8 — Create IAM Role for API Gateway

1. IAM → Roles → Create role
2. Trusted entity: **AWS Service → API Gateway**
3. Name: `apigateway-sqs-role`
4. Attach policy: `AmazonSQSFullAccess`
5. Create role → copy the **Role ARN**

---

## Step 9 — Create API Gateway

1. AWS Console → API Gateway → Create API → REST API
2. Name: `orders-api`
3. Create resource: `/orders`
4. Create method: **POST** on `/orders`
   - Integration type: Lambda function
   - Enable **Lambda proxy integration** toggle ON
   - Select `order-processor`
5. Create resource: `{order_id}` under `/orders`
6. Create method: **GET** on `/{order_id}`
   - Integration type: Lambda function
   - Enable **Lambda proxy integration** toggle ON
   - Select `order-processor`
7. Enable CORS on `/orders` — check POST
8. Enable CORS on `/{order_id}` — check GET
9. Deploy API → stage name: `prod`
10. Copy the **Invoke URL**

---

## Step 10 — Create API Key

1. API Gateway → API keys → Create API key
2. Name: `orders-api-key` → Save
3. API Gateway → Usage plans → Create
   - Name: `orders-plan`
   - Rate: `100` req/sec, Burst: `200`, Quota: `10000`/month
4. Add API stage: `orders-api` → `prod`
5. Add API key: `orders-api-key`
6. Go to POST method → Method request → Edit → API key required: `true`
7. Do the same for GET method
8. Redeploy API → `prod`
9. Copy the **API key value** from API keys page

---

## Step 11 — Run the Frontend

1. Open `frontend/index.html`
2. Replace `YOUR_API_URL` with your Invoke URL
3. Replace `YOUR_API_KEY` with your API key value
4. Open in browser
