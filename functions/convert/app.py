from re import compile, IGNORECASE
from uuid import uuid4
from os import environ
from io import StringIO
from contextlib import redirect_stdout
from logging import getLogger
from urllib.parse import unquote_plus
from json import dumps
from pathlib import Path
from boto3 import client
from tscribe import write as docx_writer


s3_client = client("s3")
valid_docket_type1 = compile(r"P\d+-\w{2}\d{2}", flags=IGNORECASE)
valid_docket_type2 = compile(r"\w{3}-\d{3}\w{2}\d{2}")
logger = getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    common_filename = environ.get("COMMON_FILENAME")
    if not common_filename:
        raise Exception("Cannot find env COMMON_FILENAME")

    logger.info("## EVENT")
    logger.info(dumps(event, indent=2))

    # key includes directory path (e.g., transcribed/P12345-US01)
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    # Docket only
    docket = get_docket(key)
    download_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    upload_bucket = download_bucket
    # Create a path in the Lambda tmp directory to save the file to
    download_path = f"/tmp/{uuid4()}.json"
    # Create another path to save the encrypted file to
    upload_path = f"/tmp/converted-{uuid4()}.docx"

    download_file(download_bucket, key, download_path)
    new_key = make_new_key(docket, common_filename)
    result = make_docx_file(download_path, upload_path)
    upload_file(upload_path, upload_bucket, new_key)

    logger.info("## DONE")
    logger.info(result)


def download_file(download_bucket, key, download_path):
    s3_client.download_file(download_bucket, key, download_path)
    logger.info("file downloaded")


def upload_file(upload_path, upload_bucket, new_key):
    s3_client.upload_file(upload_path, upload_bucket, new_key)
    logger.info("file uploaded")


def make_docx_file(download_path, upload_path):
    with StringIO() as buf, redirect_stdout(buf):
        try:
            docx_writer(download_path, save_as=upload_path)
        except Exception as e:
            raise Exception(f"Failed to create docx: {str(e)}")
        result = buf.getvalue()
    return result


def make_new_key(docket, common_filename):
    return f"converted/{docket} {common_filename}.docx"


def get_docket(filename):
    path = Path(filename)
    match = valid_docket_type1.search(path.stem) or valid_docket_type2.search(path.stem)
    if match:
        return match.group(0).upper()
    else:
        raise Exception(f"Could not find a valid docket number in: {path.stem}")
