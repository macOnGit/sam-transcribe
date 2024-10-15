import json
import pytest


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
@pytest.mark.parametrize(
    "log_events", ["/aws/lambda/sam-transcribe-RunTranscriptionJob"], indirect=True
)
def test_lambda_invoked(log_events):
    success_found = False
    for event in log_events:
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
