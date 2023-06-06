import boto3
import json
import os

sf = boto3.client("stepfunctions")
sns = boto3.client("sns")

cloudwatch_url = "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/opas-data-utility-staging/log-events/ecs$252Fmain$252F"
stepfunctions_url = "https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1#/v2/executions/details/"

def handler(event, context):

    sf_response = sf.get_execution_history(
        executionArn=event["executionArn"],
        maxResults=1000
    )

    task_submissions = [event for event in sf_response["events"] if event["type"] == "TaskSubmitted"]

    msg = "Task execution logs \n\n"
    msg += f"Execution details: {stepfunctions_url}{event['executionArn']} \n\n"

    for task_submission in task_submissions:
        output = json.loads(task_submission["taskSubmittedEventDetails"]["output"])

        TaskArn = output["Tasks"][0]["Containers"][0]["TaskArn"]
        execution_id = TaskArn.split("/")[-1]

        environment_overrides = output["Tasks"][0]["Overrides"]["ContainerOverrides"][0]["Environment"]
        utility_args = [env["Value"] for env in environment_overrides if env["Name"] == "UTILITY_ARGS"][0]
        utility_name = [env["Value"] for env in environment_overrides if env["Name"] == "UTILITY_NAME"][0]
        
        msg += f"Utility: {utility_name}\n"
        msg += f"Arguments: {utility_args}\n"
        msg += f"{cloudwatch_url}{execution_id}\n\n"

    

    subject = f"Data Utility: {event['executionArn'].split(':')[-1]}"

    sns.publish(
        TargetArn=os.environ["SNS_TOPIC_ARN"],
        Message=msg,
        Subject=subject
    )