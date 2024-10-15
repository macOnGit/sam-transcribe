import pytest
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
@pytest.mark.parametrize(
    "log_events", ["/aws/lambda/sam-transcribe-ConvertToDocx"], indirect=True
)
def test_lambda_invoked(log_events):
    success_found = False
    for event in log_events:
        try:
            message = json.loads(event["message"])
        except json.decoder.JSONDecodeError:
            continue
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
