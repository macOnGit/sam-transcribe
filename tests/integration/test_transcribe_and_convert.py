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
