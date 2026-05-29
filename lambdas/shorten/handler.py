import json
import boto3
import os
import random
import string
from datetime import datetime

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
BASE_URL = os.environ.get("BASE_URL", "http://localhost")

def generate_code(length=6):
    """Generate a random 6-character alphanumeric code."""
    chars = string.ascii_letters + string.digits   # a-z A-Z 0-9
    return "".join(random.choices(chars, k=length))

def lambda_handler(event, context):
    """
    Called when POST /shorten is hit.
    Expects: { "url": "https://example.com/long-url" }
    Returns: { "short_url": "https://short.ly/ab3k7f" }
    """
    # Parse request body
    body = json.loads(event.get("body", "{}"))
    original_url = body.get("url", "").strip()

    # Validate input
    if not original_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing url in request body"})
        }

    if not original_url.startswith("http"):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "URL must start with http or https"})
        }

    # Generate a unique code
    code = generate_code()

    # Save to DynamoDB
    table.put_item(Item={
        "code": code,
        "original_url": original_url,
        "created_at": datetime.utcnow().isoformat()
    })

    short_url = f"{BASE_URL}/{code}"

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "short_url": short_url,
            "code": code,
            "original_url": original_url
        })
    }