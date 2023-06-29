import boto3
import json
import os

sns = boto3.client("sns")

cloudwatch_url = "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/opas-data-utility-staging/log-events/ecs$252Fmain$252F"
stepfunctions_url = "https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1#/v2/executions/details/"

def handler(event, context):
    print("Event: ", event)

    parsed_error = json.loads(event["task"]["error"]["Cause"])
    taskArn = parsed_error["TaskArn"]
    execution_id = taskArn.split("/")[-1]

    print("Parsed error: ", parsed_error)

    msg = "Job execution failed \n\n"
    msg += f"Execution details: {stepfunctions_url}{event['executionArn']} \n\n"
    msg += f"Utility: {event['task']['utility']}\n"
    msg += f"Arguments: {event['task']['args']}\n"
    msg += f"{cloudwatch_url}{execution_id}\n\n"

    subject = f"Data Utility: {event['executionArn'].split(':')[-1]}"
    
    sns.publish(
        TargetArn=os.environ["SNS_TOPIC_ARN"],
        Message=msg,
        Subject=subject
    )

    return event["task"]