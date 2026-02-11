import json
from urllib.parse import unquote
from step_function_manager import stop_existing_executions, start_new_execution

SMARTLOAD_TRIGGER_BUILDS = ("(bKBD3)", "(bSeriesTOC)")


def parse_key(key):
    """
    Example:
      key = _PEPFree/RGK/2020/2/finafiwang.xml
      sub -> _PEPFree/RGK/2020/2
      artId -> finafiwang
    """
    # Remove any leading/trailing slashes just in case
    keyParts = key.split("/")
    sub = keyParts[0]
    artId = keyParts[-1].split("(")[0]

    return sub, artId

def handler(event, context):
    print(event)

    # Dictionary mapping sub -> set of artIds
    sub_articles_map = {}

    for sqs_record in event["Records"]:
        # Convert body to dict if it is a JSON string
        body = (
            json.loads(sqs_record["body"])
            if isinstance(sqs_record["body"], str)
            else sqs_record["body"]
        )

        for record in body["Records"]:
            key = unquote(record["s3"]["object"]["key"])

            # Skip future and non-source builds (smartload should run only from source XML builds).
            if "_PEPFuture" in key:
                continue
            if not any(build in key for build in SMARTLOAD_TRIGGER_BUILDS):
                continue

            # Parse the key into sub and artId properly
            sub, artId = parse_key(key)

            if sub not in sub_articles_map:
                sub_articles_map[sub] = set()

            sub_articles_map[sub].add(artId)

    # Now you have a dictionary of { sub: {artId1, artId2, ...}, ... }
    # Decide whether to run separate Step Function executions per article
    # or combine them into one execution per sub.

    for sub, artIds in sub_articles_map.items():
        if not artIds:
            continue
        combined_keys_regex = "|".join(sorted(artIds))
        stop_existing_executions(sub, combined_keys_regex)
        start_new_execution(sub, combined_keys_regex)
