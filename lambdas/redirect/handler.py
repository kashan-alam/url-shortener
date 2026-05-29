import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    """
    Called when GET /{code} is hit.
    Looks up the code in DynamoDB.
    Returns a 301 redirect to the original URL.
    """
    # Extract the code from the URL path
    code = event.get("pathParameters", {}).get("code", "")

    if not code:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No code provided"})
        }

    # Look up in DynamoDB
    response = table.get_item(Key={"code": code})
    item = response.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"Short code '{code}' not found"})
        }

    # Return redirect
    return {
        "statusCode": 301,
        "headers": {
            "Location": item["original_url"]
        },
        "body": ""
    }