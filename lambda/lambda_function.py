import json
import logging
import boto3
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('orders')
sqs      = boto3.client('sqs')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/orders-queue'

# DynamoDB stores numbers as Decimal — convert back for JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}


def lambda_handler(event, context):
    # API Gateway request (GET or POST)
    if 'httpMethod' in event:
        return handle_api_request(event)
    # SQS trigger
    return handle_sqs_messages(event)


# ── API Gateway handler ────────────────────────────────────────────
def handle_api_request(event):
    method = event['httpMethod']
    logger.info(f"API request: {method}")

    if method == 'GET':
        order_id = event['pathParameters']['order_id']
        return get_order(order_id)

    if method == 'POST':
        body = json.loads(event['body'])
        return post_order(body)

    return {'statusCode': 405, 'headers': CORS_HEADERS, 'body': json.dumps('Method not allowed')}


def post_order(body):
    """Validate then send to SQS"""

    # ── Validation ─────────────────────────────────────────────────
    errors = []

    for field in ['order_id', 'item', 'qty', 'user_id']:
        if field not in body:
            errors.append(f"Missing required field: {field}")

    if 'qty' in body:
        if not isinstance(body['qty'], (int, float)):
            errors.append("qty must be a number")
        elif body['qty'] <= 0:
            errors.append("qty must be greater than 0")

    for field in ['order_id', 'item', 'user_id']:
        if field in body and not str(body[field]).strip():
            errors.append(f"{field} cannot be empty")

    if errors:
        logger.info(f"Validation failed: {errors}")
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Validation failed', 'details': errors})
        }

    # ── Send to SQS ────────────────────────────────────────────────
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(body)
    )

    # ── Save immediately to DynamoDB with pending status ───────────
    table.put_item(Item={
        'order_id':   body['order_id'],
        'item':       body['item'],
        'qty':        body['qty'],
        'user_id':    body['user_id'],
        'status':     'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    })

    logger.info(f"Order {body['order_id']} saved as pending, sent to SQS")
    return {
        'statusCode': 202,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'message': 'Order accepted',
            'order_id': body['order_id']
        })
    }


def get_order(order_id):
    """Fetch order from DynamoDB"""
    logger.info(f"Fetching order #{order_id}")
    response = table.get_item(Key={'order_id': order_id})

    if 'Item' not in response:
        return {
            'statusCode': 404,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': f'Order {order_id} not found'})
        }

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps(response['Item'], cls=DecimalEncoder)
    }


# ── SQS handler ────────────────────────────────────────────────────
def handle_sqs_messages(event):
    logger.info(f"Received {len(event['Records'])} order(s) from SQS")

    for record in event['Records']:
        body       = json.loads(record['body'])
        message_id = record['messageId']
        order_id   = body.get('order_id', 'unknown')

        # Update status to processing immediately
        table.update_item(
            Key={'order_id': order_id},
            UpdateExpression='SET #s = :s',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'processing'}
        )

        logger.info(f"Order #{order_id} status updated to processing")

        # Idempotency check — skip if already processed
        existing = table.get_item(Key={'order_id': order_id})
        if 'Item' in existing:
            logger.info(f"Order #{order_id} already processed — skipping")
            continue

        # Update status to processed in DynamoDB
        table.update_item(
            Key={'order_id': order_id},
            UpdateExpression='SET #s = :s, message_id = :m',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'processed',
                ':m': message_id
            }
        )

        logger.info(f"Order #{order_id} updated to processed")

    return {
        'statusCode': 200,
        'body': json.dumps('Orders processed successfully')
    }