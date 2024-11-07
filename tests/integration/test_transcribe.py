import pytest


@pytest.mark.order(1)
def test_file_upload(s3_client, bucket, files_for_tests):
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
    "log_client_func", ["/aws/lambda/sam-transcribe-RunTranscriptionJob"], indirect=True
)
def test_lambda_invoked(log_client_func):
    log_client_func()


# @pytest.mark.order(3)
# def test_cleanup(cleanup_test_files, delete_test_job):
#     # TODO: need way to specify which items to delete per test

#     # items to delete:
#     # 1. uploaded audio
#     # 2. transcribed audio file
#     # 3. converted docx file
#     # 4. transcription job
#     pass
