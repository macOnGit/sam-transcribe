import pytest
import pprint
import json
from pathlib import Path
from dataclasses import dataclass
import boto3
import tomllib
import re
import os
import time
from moto import mock_aws


base_path = Path(__file__).parent
MAX_WAIT = 5
MAX_DEL_ATTEMPTS = 45


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
    generated_converted: str
    generated_transcription: str
    transcription_job_name: str


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
    match = re.search(
        'TranscribeBucketName="((?!(^xn--|.+-s3alias$))[a-z0-9][a-z0-9-]{1,61}[a-z0-9])"',
        samconfig_params,
    )

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
    match = re.search('CommonFilename="([ a-zA-Z0-9!_.*\'()-]+)"', samconfig_params)
    if not match:
        raise Exception("Could not find CommonFileName in samconfig")
    return match.group(1)


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
def docx_file():
    # return first docx file found in folder
    fixtures_path = base_path / "fixtures"
    for child in fixtures_path.iterdir():
        if child.suffix == ".docx":
            return child


@pytest.fixture(scope="session")
def files_for_tests(
    audio_file,
    json_file,
    docx_file,
    test_docket_number,
    common_filename,
):
    if not audio_file:
        raise Exception("Could not find test audio file")

    if not json_file:
        raise Exception("Could not find test transcribed file")

    if not docx_file:
        raise Exception("Could not find test converted file")

    return FileNames(
        audio=audio_file,
        transcribed=json_file,
        converted=docx_file,
        generated_converted=f"{test_docket_number} {common_filename}.docx",
        generated_transcription=f"{test_docket_number}.json",
        transcription_job_name=f"audiotojson-{test_docket_number}",
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


@pytest.fixture
def log_client_func(logs_client, request):
    logGroupName = request.param

    def inner_func():

        start_time = time.time()

        while True:
            # Get the latest log stream for the specified log group
            try:
                log_streams = logs_client.describe_log_streams(
                    logGroupName=logGroupName,
                    orderBy="LastEventTime",
                    descending=True,
                    limit=1,
                )
            except logs_client.exceptions.ResourceNotFoundException:
                continue

            latest_log_stream_name = log_streams["logStreams"][0]["logStreamName"]
            # Retrieve the log events from the latest log stream
            log_events = logs_client.get_log_events(
                logGroupName=logGroupName,
                logStreamName=latest_log_stream_name,
            )

            # Check the log events
            success_found = False
            for event in log_events["events"]:
                try:
                    message = json.loads(event["message"])
                except json.decoder.JSONDecodeError:
                    continue
                status = message.get("record", {}).get("status")
                if status == "success":
                    success_found = True
                    break

            try:
                assert (
                    success_found
                ), "Lambda function execution did not report 'success' status in logs."
                break
            except AssertionError as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(1)

    return inner_func


@pytest.fixture(scope="session")
def s3_objects_to_delete(bucket, files_for_tests):
    return [
        {
            # Delete uploaded audio file
            "Key": f"{bucket.audio}/{files_for_tests.audio.name}"
        },
        {
            # Delete uploaded transcribed file
            "Key": f"{bucket.transcribed}/{files_for_tests.transcribed.name}"
        },
        {
            # Delete uploaded converted file
            "Key": f"{bucket.converted}/{files_for_tests.converted.name}"
        },
        {
            # Delete generated transcribed file
            "Key": f"{bucket.transcribed}/{files_for_tests.generated_transcription}"
        },
        {
            # Delete generated converted file
            "Key": f"{bucket.converted}/{files_for_tests.generated_converted}"
        },
    ]


@pytest.fixture(scope="session")
def delete_test_job(files_for_tests):
    transcribe = boto3.client("transcribe")

    yield
    # Cleanup code will be executed after all tests have finished
    job_del_attempts = 0
    error = None

    while True:
        try:
            transcribe.delete_transcription_job(
                TranscriptionJobName=files_for_tests.transcription_job_name
            )
            print(
                f"Deleted transcription job: {files_for_tests.transcription_job_name}"
            )
            break
        except transcribe.exceptions.BadRequestException:
            print(
                f"Transcription job to del not found: {files_for_tests.transcription_job_name}"
            )
            break
        except Exception as e:
            error = e
            job_del_attempts += 1
        if job_del_attempts >= MAX_DEL_ATTEMPTS:
            print(
                f"After max attempts, could not delete transcription job: {str(error)}"
            )
            break
        time.sleep(1)


@pytest.fixture(scope="session")
def cleanup_test_files(bucket, s3_objects_to_delete):
    # Create a new S3 client for cleanup
    s3_client = boto3.client("s3")

    yield
    # Cleanup code will be executed after all tests have finished
    objs_deleted = 0
    obj_del_attempts = 0

    while True:
        response = s3_client.delete_objects(
            Bucket=bucket.base,
            Delete={"Objects": s3_objects_to_delete},
        )
        print("Response:")
        pprint.pp(response, indent=2)
        objs_deleted += len(response["Deleted"])
        if objs_deleted == len(s3_objects_to_delete):
            break
        if obj_del_attempts >= MAX_DEL_ATTEMPTS:
            raise Exception("Could not delete all objects from bucket")
        obj_del_attempts += 1
        time.sleep(1)
