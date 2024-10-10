import pytest
import json
from pathlib import Path
from dataclasses import dataclass
import boto3
import os
from dotenv import load_dotenv


base_path = Path(__file__).parent


@pytest.fixture
def event(request):
    filename = request.param
    json_file = base_path / "events" / f"{filename}.json"
    with json_file.open() as fp:
        fixture = json.load(fp)
    return fixture


@dataclass
class Bucket:
    base: str
    audio: str
    transcribed: str
    converted: str


@dataclass
class FileNames:
    audio: str
    transcribed: str
    converted: str
    fixtures_path: Path


@pytest.fixture(scope="session")
def _load_dotenv():
    load_dotenv()


@pytest.fixture(scope="session")
def bucket(_load_dotenv):
    base = os.environ.get("TEST_BUCKET_NAME")
    if not base:
        raise Exception("Cannot find env TEST_BUCKET_NAME")
    return Bucket(
        base=base,
        audio=f"audio",
        transcribed=f"transcribed",
        converted=f"converted",
    )


@pytest.fixture(scope="session")
def file_names(_load_dotenv):
    audio = os.environ.get("TEST_AUDIO_FILE_NAME")
    if not audio:
        raise Exception("Cannot find env TEST_AUDIO_FILE_NAME")

    transcribed = os.environ.get("TEST_TRANSCRIBED_FILE_NAME")
    if not transcribed:
        raise Exception("Cannot find env TEST_TRANSCRIBED_FILE_NAME")

    converted = os.environ.get("TEST_CONVERTED_FILE_NAME")
    if not converted:
        raise Exception("Cannot find env TEST_CONVERTED_FILE_NAME")

    return FileNames(
        audio=audio,
        transcribed=transcribed,
        converted=converted,
        fixtures_path=base_path / "fixtures",
    )


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
def cleanup(bucket, file_names):
    # Create a new S3 client for cleanup
    s3_client = boto3.client("s3")

    yield
    # Cleanup code will be executed after all tests have finished

    # Delete test audio file from bucket
    bucket_key = f"{bucket.audio}/{file_names.audio}"
    s3_client.delete_object(Bucket=bucket.base, Key=bucket_key)
    print(f"\nDeleted {file_names.audio} from {bucket.base}")
