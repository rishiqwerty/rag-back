import json
from app.services.ingestion import process_document


def lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        task_id = int(body["task_id"])

        print(f"Processing task_id: {task_id}")
        process_document(task_id)
        print(f"Completed processing task_id: {task_id}")

    return {"statusCode": 200, "body": json.dumps("Processed all tasks successfully")}
