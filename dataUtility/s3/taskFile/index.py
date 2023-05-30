import boto3
import json
import os
import uuid

sf = boto3.client("stepfunctions")

def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        sf_response = sf.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=str(uuid.uuid4()),
            input=json.dumps([]),
        )
        
