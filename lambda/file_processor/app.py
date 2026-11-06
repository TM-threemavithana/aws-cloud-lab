import json
import logging
from urllib.parse import unquote_plus

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_FILE_BYTES = 65536


def lambda_handler(event, context):
    records = event.get("Records", [])

    if not records:
        raise ValueError("No S3 event records supplied")

    s3 = boto3.client("s3")
    processed = []

    for record in records:
        if record.get("eventSource") != "aws:s3":
            raise ValueError("Not an S3 event")

        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        if not key.startswith("incoming/") or not key.endswith(".json"):
            raise ValueError("Unexpected object key")

        response = s3.get_object(Bucket=bucket, Key=key)

        if response["ContentLength"] > MAX_FILE_BYTES:
            raise ValueError("File exceeds size limit")

        body = response["Body"].read(MAX_FILE_BYTES + 1)

        if len(body) > MAX_FILE_BYTES:
            raise ValueError("File exceeds size limit")

        try:
            document = json.loads(body)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Invalid JSON document") from exc

        if not isinstance(document, dict):
            raise ValueError("Expected a JSON object")

        for field in ("document_id", "type"):
            if not isinstance(document.get(field), str) or not document[field].strip():
                raise ValueError(f"Missing or invalid field: {field}")

        logger.info("Successfully processed object: %s/%s", bucket, key)

        processed.append({
            "bucket": bucket,
            "key": key,
            "document_id": document["document_id"],
            "type": document["type"],
        })

    return {
        "status": "processed",
        "count": len(processed),
        "objects": processed,
    }
