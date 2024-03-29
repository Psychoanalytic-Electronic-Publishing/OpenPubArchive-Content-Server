import boto3
import json
import os

client = boto3.client("stepfunctions")

def handler(event, context):
    print(event)

    try:
        response = client.list_executions(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            statusFilter='RUNNING',
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