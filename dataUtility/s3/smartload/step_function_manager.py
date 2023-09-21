import json
import uuid
import boto3
import os
from utils import list_all_running_executions, get_payload

sf = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def stop_existing_executions(sub, artId):
    executions_to_cancel = []
    expected_payload = get_payload(sub, artId)

    running_executions = list_all_running_executions(STATE_MACHINE_ARN)
    for execution in running_executions:
        execution_detail = sf.describe_execution(
            executionArn=execution["executionArn"])
        execution_input = json.loads(execution_detail["input"])

        if execution_input == expected_payload:
            executions_to_cancel.append(execution["executionArn"])

    for execution_arn in executions_to_cancel:
        sf.stop_execution(executionArn=execution_arn)


def start_new_execution(sub, artId):
    payload = get_payload(sub, artId)
    sf.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=str(uuid.uuid4()),
        input=json.dumps(payload)
    )
