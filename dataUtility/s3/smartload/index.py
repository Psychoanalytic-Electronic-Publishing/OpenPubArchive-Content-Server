from urllib.parse import unquote
from step_function_manager import stop_existing_executions, start_new_execution


def handler(event, context):
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        key = unquote(key)

        if "(bKBD3)" not in key:
            continue

        keyParts = key.split("/")
        sub = keyParts[0]
        artId = keyParts[-1].split("(")[0]

        stop_existing_executions(sub, artId)
        start_new_execution(sub, artId)
