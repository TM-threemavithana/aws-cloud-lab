import json
import sys
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "lambda/file_processor")
)

from app import lambda_handler

BUCKET = "aws-cloud-lab-test-bucket"
KEY = "incoming/sample.json"


@pytest.fixture
def s3_client(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield client


def make_event(key=KEY):
    return {
        "Records": [{
            "eventSource": "aws:s3",
            "s3": {
                "bucket": {"name": BUCKET},
                "object": {"key": key},
            },
        }],
    }


def upload(s3_client, content, key=KEY):
    s3_client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=content,
    )


def test_valid_document(s3_client):
    upload(s3_client, json.dumps({
        "document_id": "DOC-001",
        "type": "report",
    }))

    result = lambda_handler(make_event(), None)

    assert result["status"] == "processed"
    assert result["count"] == 1
    assert result["objects"][0]["document_id"] == "DOC-001"


def test_invalid_json(s3_client):
    upload(s3_client, "not valid json")

    with pytest.raises(ValueError, match="Invalid JSON"):
        lambda_handler(make_event(), None)


def test_missing_required_field(s3_client):
    upload(s3_client, json.dumps({"document_id": "DOC-001"}))

    with pytest.raises(ValueError, match="type"):
        lambda_handler(make_event(), None)


def test_invalid_prefix(s3_client):
    with pytest.raises(ValueError, match="Unexpected object key"):
        lambda_handler(make_event("other/sample.json"), None)


def test_missing_s3_object(s3_client):
    with pytest.raises(ClientError):
        lambda_handler(make_event(), None)


def test_oversized_document(s3_client):
    upload(s3_client, "x" * 65537)

    with pytest.raises(ValueError, match="size limit"):
        lambda_handler(make_event(), None)


def test_empty_event():
    with pytest.raises(ValueError, match="No S3 event"):
        lambda_handler({"Records": []}, None)


def test_reject_non_s3_event(s3_client):
    event = make_event()
    event["Records"][0]["eventSource"] = "aws:sns"

    with pytest.raises(ValueError, match="Not an S3 event"):
        lambda_handler(event, None)


def test_reject_non_json_extension(s3_client):
    with pytest.raises(ValueError, match="Unexpected object key"):
        lambda_handler(make_event("incoming/file.txt"), None)


def test_reject_json_array(s3_client):
    upload(s3_client, '["item1", "item2"]')

    with pytest.raises(ValueError, match="Expected a JSON object"):
        lambda_handler(make_event(), None)


def test_url_encoded_s3_key(s3_client):
    from urllib.parse import quote_plus

    key = "incoming/monthly report.json"

    upload(s3_client, json.dumps({
        "document_id": "DOC-002",
        "type": "report",
    }), key=key)

    result = lambda_handler(make_event(quote_plus(key)), None)

    assert result["count"] == 1
    assert result["objects"][0]["key"] == key


def test_multiple_s3_records(s3_client):
    keys = [
        "incoming/first.json",
        "incoming/second.json",
    ]

    for index, key in enumerate(keys):
        upload(s3_client, json.dumps({
            "document_id": f"DOC-{index}",
            "type": "report",
        }), key=key)

    event = make_event(keys[0])
    event["Records"].append(make_event(keys[1])["Records"][0])

    result = lambda_handler(event, None)

    assert result["status"] == "processed"
    assert result["count"] == 2
