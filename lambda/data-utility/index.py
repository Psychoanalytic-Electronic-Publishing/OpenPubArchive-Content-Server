import subprocess
import os
import boto3

s3 = boto3.client("s3")

def execute(cmd, cwd=None):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, cwd=cwd)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)



def handler(event, context):
    # Check if each event param is present
    if "utility" not in event:
        raise TypeError("utility param not provided")

    if "commands" not in event:
        raise TypeError("command param not provided")

    # Select working directory based on utility
    if (
        event["utility"] == "opasDataLoader"
        or event["utility"] == "opasDataCleaner"
        or event["utility"] == "opasDataLinker"
        or event["utility"] == "opasBuildControl"
    ):
        cwd = os.path.abspath("./opasDataLoader")
    else:
        cwd = os.path.abspath(f"./{event['utility']}")

    cmd = ["python", f"{event['utility']}.py"] + event["commands"]

    print(f"Executing command: {cmd} in {cwd}")

    # Execute commands
    for path in execute(cmd, cwd=cwd):
        print(path, end="")
