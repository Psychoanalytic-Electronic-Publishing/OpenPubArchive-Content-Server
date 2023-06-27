import boto3
import json
import os
import uuid

sf = boto3.client("stepfunctions")
s3 = boto3.resource('s3')

def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        obj = s3.Object(bucket, key)
        body = obj.get()['Body'].read().decode('utf-8')

        trigger_env = key.split("/")[0]

        arn = ""

        if trigger_env == "run_staging":
            arn = os.environ["STAGING_STATE_MACHINE_ARN"]

        elif trigger_env == "run_production":
            arn = os.environ["PRODUCTION_STATE_MACHINE_ARN"]

        sf_response = sf.start_execution(
            stateMachineArn=arn,
            name=str(uuid.uuid4()),
            input=json.dumps(json.loads(str(body))),
        )

        obj.delete()