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
