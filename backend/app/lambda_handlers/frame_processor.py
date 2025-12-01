"""
Lambda handler for processing video frames from ESP32.
"""

import json
import base64
import boto3
from datetime import datetime, timedelta

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')


def handler(event, context):
    """
    Process uploaded video frame.

    Event from API Gateway:
    {
        "device_id": "ESP32_001",
        "vehicle_id": 1,
        "camera_position": "FRONT",
        "frame_base64": "..."
    }
    """
    try:
        # Parse body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        device_id = body['device_id']
        vehicle_id = body['vehicle_id']
        camera_position = body.get('camera_position', 'FRONT')
        frame_base64 = body['frame_base64']

        # Decode frame
        frame_bytes = base64.b64decode(frame_base64)

        # Generate S3 key
        timestamp = datetime.utcnow()
        s3_key = f"frames/vehicle_{vehicle_id}/{timestamp.strftime('%Y/%m/%d/%H%M%S')}.jpg"

        # Upload to S3
        s3_bucket = 'taxiwatch-frames'  # From environment variable
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=frame_bytes,
            ContentType='image/jpeg',
            Metadata={
                'device_id': device_id,
                'vehicle_id': str(vehicle_id),
                'camera_position': camera_position
            }
        )

        # Enqueue for AI analysis
        sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/...'  # From env
        sqs_client.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps({
                'vehicle_id': vehicle_id,
                's3_bucket': s3_bucket,
                's3_key': s3_key,
                'timestamp': timestamp.isoformat()
            })
        )

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Frame uploaded successfully',
                's3_key': s3_key
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
