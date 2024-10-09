from dataclasses import dataclass
from pathlib import Path
import boto3
import json
import pytest
import time
import os
from dotenv import load_dotenv

base_path = Path(__file__).parents[2]
fixtures_path = base_path / "fixtures"


@dataclass
class Bucket:
    base: str
    audio: str
    transcribed: str
    converted: str


@dataclass
class FileNames:
    audio: str
    transcribed: str
    converted: str


@pytest.fixture(scope="session")
def _load_dotenv():
    load_dotenv()


@pytest.fixture(scope="session")
def bucket(_load_dotenv):
    base = os.environ.get("TEST_BUCKET_NAME")
    if not base:
        raise Exception("Cannot find env TEST_BUCKET_NAME")
    return Bucket(
        base=base,
        audio=f"/audio",
        transcribed=f"/transcribed",
        converted=f"/converted",
    )


@pytest.fixture(scope="session")
def file_names(_load_dotenv):
    audio = os.environ.get("TEST_AUDIO_FILE_NAME")
    if not audio:
        raise Exception("Cannot find env TEST_AUDIO_FILE_NAME")

    transcribed = os.environ.get("TEST_TRANSCRIBED_FILE_NAME")
    if not transcribed:
        raise Exception("Cannot find env TEST_TRANSCRIBED_FILE_NAME")

    converted = os.environ.get("TEST_CONVERTED_FILE_NAME")
    if not converted:
        raise Exception("Cannot find env TEST_CONVERTED_FILE_NAME")

    return FileNames(
        audio=audio,
        transcribed=transcribed,
        converted=converted,
    )


@pytest.fixture
def lambda_client():
    return boto3.client("lambda")


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture
def logs_client():
    return boto3.client("logs")


@pytest.fixture(scope="session")
def cleanup(bucket, file_names):
    # Create a new S3 client for cleanup
    s3_client = boto3.client("s3")

    yield
    # Cleanup code will be executed after all tests have finished

    # Delete test audio file from bucket
    bucket_key = f"{bucket.audio}/{file_names.audio}"
    s3_client.delete_object(Bucket=bucket.base, Key=bucket_key)
    print(f"\nDeleted {file_names.audio} from {bucket.base}")


@pytest.mark.order(1)
def test_source_bucket_audio_available(s3_client, bucket, file_names):
    s3_bucket_name = bucket.base
    file_path = str(fixtures_path / file_names.audio)
    prefixed_file_name = f"{bucket.audio}/{file_names.audio}"

    file_uploaded = False

    try:
        s3_client.upload_file(file_path, s3_bucket_name, prefixed_file_name)
        file_uploaded = True
    except Exception as err:
        print(str(err))

    assert file_uploaded, "Could not upload file to S3 bucket"


@pytest.mark.order(2)
def test_lambda_invoked(logs_client):

    # Wait for a few seconds to make sure the logs are available
    time.sleep(5)

    # Get the latest log stream for the specified log group
    log_streams = logs_client.describe_log_streams(
        logGroupName="/aws/lambda/RunTranscriptionJob",
        orderBy="LastEventTime",
        descending=True,
        limit=1,
    )

    latest_log_stream_name = log_streams["logStreams"][0]["logStreamName"]

    # Retrieve the log events from the latest log stream
    log_events = logs_client.get_log_events(
        logGroupName=f"/aws/lambda/RunTranscriptionJob",
        logStreamName=latest_log_stream_name,
    )

    success_found = False
    for event in log_events["events"]:
        message = json.loads(event["message"])
        status = message.get("record", {}).get("status")
        if status == "success":
            success_found = True
            break

    assert (
        success_found
    ), "Lambda function execution did not report 'success' status in logs."


"""
@pytest.mark.order(3)
def test_encrypted_file_in_bucket(s3_client):
    # Specify the destination S3 bucket and the expected converted file key
    destination_bucket = DESTINATION_BUCKET
    converted_file_key = "test_encrypted.pdf"

    try:
        # Attempt to retrieve the metadata of the converted file from the destination S3 bucket
        s3_client.head_object(Bucket=destination_bucket, Key=converted_file_key)
    except s3_client.exceptions.ClientError as e:
        # If the file is not found, the test will fail
        pytest.fail(
            f"Converted file '{converted_file_key}' not found in the destination bucket: {str(e)}"
        )
"""


def test_cleanup(cleanup):
    # This test uses the cleanup fixture and will be executed last
    pass
