import boto3
import json
import os

sns = boto3.client("sns")

stepfunctions_url = "https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1#/v2/executions/details/"

def handler(event, context):
    print("Event: ", event)

    msg = "Job execution failed \n\n"
    msg += f"Execution details: {stepfunctions_url}{event['executionArn']} \n\n"
    msg += f"Utility: {event['task']['utility']}\n"
    msg += f"Arguments: {event['task']['args']}\n"

    subject = f"Data Utility: {event['executionArn'].split(':')[-1]}"
    
    sns.publish(
        TargetArn=os.environ["SNS_TOPIC_ARN"],
        Message=msg,
        Subject=subject
    )

    return event["task"]