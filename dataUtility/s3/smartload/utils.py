import boto3

sf = boto3.client("stepfunctions")


def list_all_running_executions(state_machine_arn):
    next_token = None
    executions = []

    while True:
        if next_token:
            list_executions_response = sf.list_executions(
                stateMachineArn=state_machine_arn,
                statusFilter='RUNNING',
                nextToken=next_token
            )
        else:
            list_executions_response = sf.list_executions(
                stateMachineArn=state_machine_arn,
                statusFilter='RUNNING'
            )

        executions.extend(list_executions_response["executions"])

        next_token = list_executions_response.get("nextToken")
        if not next_token:
            break

    return executions


def get_payload(sub, artId):
    loadPayload = [{
        "directory": "opasDataLoader",
        "utility": "opasDataLoader",
        "args": f"--sub {sub} --key {artId} --smartload --verbose --nocheck",
    }]
    linkPayload = [{
        "directory": "opasDataLoader",
        "utility": "opasDataLinker",
        "args": f"--key {artId}",
    }]
    return [loadPayload, linkPayload, loadPayload]
