import logging
from urllib.parse import unquote_plus

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    records = event.get("Records", [])

    if not records:
        raise ValueError("No S3 event records supplied")

    objects = []

    for record in records:
        if record.get("eventSource") != "aws:s3":
            raise ValueError("Not an S3 event")

        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        if not key.startswith("incoming/"):
            raise ValueError("Unexpected object prefix")

        logger.info("Received object: %s/%s", bucket, key)

        objects.append({
            "bucket": bucket,
            "key": key
        })

    return {
        "status": "received",
        "count": len(objects),
        "objects": objects
    }
