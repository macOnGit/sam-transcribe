"""
We are testing that uploading an audio file results in a
docx file for downloading
"""

import pytest
import time


@pytest.mark.order(1)
def test_docx_is_created(s3_client, upload_bucket, download_bucket, files_for_tests):
    MAX_WAIT = 10
    start_time = time.time()

    # Upload audio file
    file_path = str(files_for_tests.audio)
    audio_file_name = files_for_tests.audio.name
    s3_client.upload_file(file_path, upload_bucket.base, audio_file_name)

    # Give it time to work
    time.sleep(5)

    # Specify the destination S3 bucket and the expected converted file key
    destination_bucket = download_bucket.base
    prefixed_converted_file_name = (
        f"{download_bucket.converted}/{files_for_tests.generated_converted}"
    )

    while True:
        try:
            # Attempt to retrieve the metadata of the converted file from the destination S3 bucket
            s3_client.head_object(
                Bucket=destination_bucket, Key=prefixed_converted_file_name
            )
            break
        except s3_client.exceptions.ClientError as e:
            # If the file is not found in given time, the test will fail
            if time.time() - start_time > MAX_WAIT:
                pytest.fail(
                    f"Converted file '{prefixed_converted_file_name}' not found in the destination bucket: {str(e)}"
                )
                break
            time.sleep(1)


# def test_cleanup(cleanup_test_files):
#     # This test uses the cleanup fixture and will be executed last
#     pass
