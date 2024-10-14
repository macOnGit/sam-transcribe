import pytest
import time
import json


@pytest.mark.order(1)
def test_source_bucket_transcribe_available(s3_client, bucket, files_for_tests):
    s3_bucket_name = bucket.base
    file_path = str(files_for_tests.transcribed)
    prefixed_file_name = f"{bucket.transcribed}/{files_for_tests.transcribed.name}"

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

    # TODO: can this not be hardcoded?
    logGroupName = "/aws/lambda/sam-transcribe-ConvertToDocx"

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


def test_cleanup(cleanup):
    # This test uses the cleanup fixture and will be executed last
    pass
