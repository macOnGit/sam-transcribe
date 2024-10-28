import pytest


@pytest.mark.order(1)
def test_source_bucket_transcribe_available(s3_client, bucket, files_for_tests):
    file_path = str(files_for_tests.transcribed)
    prefixed_file_name = f"{bucket.transcribed}/{files_for_tests.transcribed.name}"

    file_uploaded = False

    try:
        s3_client.upload_file(file_path, bucket.base, prefixed_file_name)
        file_uploaded = True
    except Exception as err:
        print(str(err))

    assert file_uploaded, "Could not upload file to S3 bucket"


@pytest.mark.order(2)
@pytest.mark.parametrize(
    "log_client_func", ["/aws/lambda/sam-transcribe-ConvertToDocx"], indirect=True
)
def test_lambda_invoked(log_client_func):
    log_client_func()


@pytest.mark.order(3)
def test_cleanup(cleanup_test_files):
    # This test uses the cleanup fixture and will be executed last
    pass
