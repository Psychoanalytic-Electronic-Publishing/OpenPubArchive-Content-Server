import boto3
import json

client = boto3.client("stepfunctions")

def handler(event, context):
    print(event)

    body = json.loads(event["body"])

    response = client.stop_execution(
        executionArn=body["executionArn"],
    )
    
    return {
        "statusCode": 200,
        "body": json.dumps(response, indent=4, sort_keys=True, default=str)
    }