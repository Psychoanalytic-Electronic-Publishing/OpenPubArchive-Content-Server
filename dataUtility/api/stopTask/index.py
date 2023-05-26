import boto3
import json

client = boto3.client("stepfunctions")

def handler(event, context):
    print(event)
    try:
        body = json.loads(event["body"])

        response = client.stop_execution(
            executionArn=body["executionArn"],
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps(response, indent=4, sort_keys=True, default=str)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(e, indent=4, sort_keys=True, default=str)
        }