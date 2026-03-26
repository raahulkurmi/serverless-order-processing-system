import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table('orders')


def lambda_handler(event, context):
    for record in event['Records']:
        body     = json.loads(record['body'])
        order_id = body.get('order_id', 'unknown')

        table.update_item(
            Key={'order_id': order_id},
            UpdateExpression='SET #s = :s',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'failed'}
        )

        logger.info(f"Order #{order_id} marked as failed")

    return {'statusCode': 200}