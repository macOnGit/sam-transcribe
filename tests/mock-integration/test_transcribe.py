def test_s3_bucket_creation(mock_s3_client):
    mock_s3_client.create_bucket(Bucket="somebucket")

    result = mock_s3_client.list_buckets()
    assert len(result["Buckets"]) == 1


def test_s3_bucket_upload(mock_s3_client, mock_upload_bucket, files_for_tests):
    s3_bucket_name = mock_upload_bucket.base
    file_path = str(files_for_tests.audio)
    filename = files_for_tests.audio.name

    file_uploaded = False

    try:
        mock_s3_client.upload_file(file_path, s3_bucket_name, filename)
        file_uploaded = True
    except Exception as err:
        print(str(err))

    assert file_uploaded, "Could not upload file to S3 bucket"
