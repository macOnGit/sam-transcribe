import json
import pytest
import time


@pytest.mark.order(1)
def test_source_bucket_audio_available(s3_client, bucket, files_for_tests):
    s3_bucket_name = bucket.base
    file_path = str(files_for_tests.audio)
    prefixed_file_name = f"{bucket.audio}/{files_for_tests.audio.name}"

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

    logGroupName = "/aws/lambda/sam-transcribe-RunTranscriptionJob"

    # Get the latest log stream for the specified log group
    log_streams = logs_client.describe_log_streams(
        logGroupName=logGroupName,
        orderBy="LastEventTime",
        descending=True,
        limit=1,
    )

    latest_log_stream_name = log_streams["logStreams"][0]["logStreamName"]

    # Retrieve the log events from the latest log stream
    log_events = logs_client.get_log_events(
        logGroupName=logGroupName,
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
