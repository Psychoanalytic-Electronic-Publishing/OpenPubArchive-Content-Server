import boto3
import json
import os
import uuid

client = boto3.client("stepfunctions")


def handler(event, context):
    print(event)

    try:
        response = client.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=str(uuid.uuid4()),
            input=event["body"],
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