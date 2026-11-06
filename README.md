# AWS Cloud Engineering Lab

A hands-on AWS cloud engineering portfolio project demonstrating
serverless computing, object storage, IAM security, infrastructure
as code, automated testing, and containerized application deployment
architecture.

## Technologies

- Python 3.12
- AWS Lambda
- Amazon S3
- AWS IAM
- AWS SAM
- AWS CloudFormation
- boto3
- Moto
- pytest
- Docker

## G01 — Serverless File Processing

The application processes S3 ObjectCreated events using an AWS
Lambda function.

Workflow:

1. An object is uploaded to the incoming/ prefix of an S3 bucket.
2. An S3 ObjectCreated event invokes Lambda.
3. Lambda retrieves the JSON object using boto3.
4. The document is validated for structure and required fields.
5. Processing results are returned and logged.

The infrastructure template defines a private S3 bucket,
a Lambda function, an event trigger, and an IAM policy restricting
object reads to the incoming/ prefix.

## Automated Testing

The project uses pytest and Moto to simulate S3 operations
without requiring an AWS account.

Current verified result: 12 tests passed.

Run tests:

    source .venv/bin/activate
    pytest -v

## Infrastructure Validation

Validate the SAM template:

    sam validate --lint --template-file infra/serverless.yaml

Build the Lambda application:

    sam build --template-file infra/serverless.yaml

## Security

- S3 public access is blocked.
- S3 server-side encryption is configured.
- Lambda object reads are scoped to the incoming/ prefix.
- JSON structure and required fields are validated.
- Input size is limited to 64 KiB.

## Verification Scope

The initial event-handling Lambda was successfully invoked locally
using AWS SAM and Docker.

The updated S3 object-processing functionality has been tested
using Moto and pytest.

No resources have been deployed to AWS.

Moto tests do not validate real AWS IAM enforcement.

## Project Status

- G00: Environment setup — complete
- G01.1: Initial Lambda invocation — complete
- G01.2: S3 object processing tests — complete
- G01.3: IAM policy configuration — committed
- G01.4: Extended test suite — 12 tests passing
- G01.5: Documentation and final verification — in progress
- G02: CloudFormation, ECS, and ALB — planned
