import boto3
import json
import os
import uuid
from urllib.parse import unquote

sf = boto3.client("stepfunctions")

def handler(event, context):
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        key = unquote(key)

        if("(bKBD3)" not in key):
            continue

        keyParts = key.split("/")
        sub = keyParts[0]
        artId = keyParts[-1].split("(")[0]

        args = f"--sub {sub} --key {artId} --smartload --verbose --nocheck"

        sf_response = sf.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=str(uuid.uuid4()),
            input=json.dumps(
                [
                    [
                        {
                            "directory": "opasDataLoader",
                            "utility": "opasDataLoader",
                            "args": args,
                        }
                    ]
                ]
            ),
        )