import pytest
import json
from pathlib import Path
from dataclasses import dataclass
import boto3
import tomllib
import re
import os
from moto import mock_aws


base_path = Path(__file__).parent


@dataclass
class Bucket:
    base: str
    audio: str
    transcribed: str
    converted: str

    @property
    def prefixes(self) -> list:
        return [self.audio, self.transcribed, self.converted]


@dataclass
class FileNames:
    audio: str
    transcribed: str
    converted: str


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def mock_s3_client(aws_credentials):
    """
    Return a mocked S3 client
    """
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def mock_bucket(mock_s3_client, bucket):
    mock_s3_client.create_bucket(Bucket=bucket.base)
    return bucket


@pytest.fixture
def event(request):
    filename = request.param
    json_file = base_path / "events" / f"{filename}.json"
    with json_file.open() as fp:
        fixture = json.load(fp)
    return fixture


@pytest.fixture(scope="session")
def samconfig_params():
    samconfig_file = base_path / "samconfig.toml"
    with samconfig_file.open("rb") as fp:
        data = tomllib.load(fp)
    return data["default"]["deploy"]["parameters"]["parameter_overrides"]


@pytest.fixture(scope="session")
def bucket(samconfig_params):
    # TODO: match AWS bucket naming rules
    match = re.search('TranscribeBucketName="([a-zA-Z0-9-]+)"', samconfig_params)
    if not match:
        raise Exception("Could not find TranscribeBucketName in samconfig")
    return Bucket(
        base=match.group(1),
        audio=f"audio",
        transcribed=f"transcribed",
        converted=f"converted",
    )


@pytest.fixture(scope="session")
def common_filename(samconfig_params):
    # TODO: match AWS bucket naming rules
    match = re.search('CommonFilename="([a-zA-Z0-9- ]+)"', samconfig_params)
    if not match:
        raise Exception("Could not find CommonFileName in samconfig")
    return match


@pytest.fixture(scope="session")
def audio_file():
    # return first audio file found in folder
    fixtures_path = base_path / "fixtures"
    for child in fixtures_path.iterdir():
        if child.suffix in [
            ".amr",
            ".flac",
            ".m4a",
            ".mp3",
            ".mp4",
            ".ogg",
            ".webm",
            ".wav",
        ]:
            return child


@pytest.fixture(scope="session")
def json_file():
    # return first json file found in folder
    fixtures_path = base_path / "fixtures"
    for child in fixtures_path.iterdir():
        if child.suffix == ".json":
            return child


@pytest.fixture(scope="session")
def test_docket_number(json_file):
    valid_docket_type1 = re.compile(r"P\d+-\w{2}\d{2}", flags=re.IGNORECASE)
    valid_docket_type2 = re.compile(r"\w{3}-\d{3}\w{2}\d{2}")
    match = valid_docket_type1.search(json_file.stem) or valid_docket_type2.search(
        json_file.stem
    )
    if match:
        return match.group(0).upper()
    else:
        raise Exception(f"Could not find a valid docket number in: {json_file.stem}")


@pytest.fixture(scope="session")
def converted_file(test_docket_number, common_filename):
    return f"{test_docket_number} {common_filename}.docx"


@pytest.fixture(scope="session")
def files_for_tests(audio_file, json_file, converted_file):
    if not audio_file:
        raise Exception("Could not find test audio file")

    if not json_file:
        raise Exception("Could not find test transcribed file")

    if not converted_file:
        raise Exception("Could not find name for test converted file")

    return FileNames(audio=audio_file, transcribed=json_file, converted=converted_file)


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
def cleanup(bucket, files_for_tests):
    # Create a new S3 client for cleanup
    s3_client = boto3.client("s3")

    yield
    # Cleanup code will be executed after all tests have finished
    for prefix in bucket.prefixes:
        # e.g., the audio test file
        filename = getattr(files_for_tests, prefix)
        key = f"{prefix}/{filename}"
        s3_client.delete_object(Bucket=bucket.base, Key=key)
        print(f"\nDeleted {filename} from {bucket.base}")

    # TODO: to delete generated transcribed file, we'll need the uuid from the logstream

    # TODO: create a lambda function which deletes completed files and sends emails
