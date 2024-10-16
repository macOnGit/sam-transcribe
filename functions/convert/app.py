import re
import uuid
import os
import io
from contextlib import redirect_stdout
import logging
from urllib.parse import unquote_plus
import json
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import tscribe


s3_client = boto3.client("s3")
valid_docket_type1 = re.compile(r"P\d+-\w{2}\d{2}", flags=re.IGNORECASE)
valid_docket_type2 = re.compile(r"\w{3}-\d{3}\w{2}\d{2}")
logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):

    common_filename = os.environ.get("COMMON_FILENAME")
    if not common_filename:
        raise Exception("Cannot find env COMMON_FILENAME")

    logger.info("## EVENT")
    logger.info(json.dumps(event, indent=2))

    # key includes directory path (e.g., transcribed/P12345-US01)
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    # Docket only
    docket = get_docket(key)
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    # Create a path in the Lambda tmp directory to save the file to
    download_path = f"/tmp/{uuid.uuid4()}.json"
    # Create another path to save the encrypted file to
    upload_path = f"/tmp/converted-{uuid.uuid4()}.docx"

    try:
        s3_client.download_file(bucket, key, download_path)
        logger.info("file downloaded")
    except ClientError as e:
        logger.error(e)
        return False

    with io.StringIO() as buf, redirect_stdout(buf):
        try:
            tscribe.write(download_path, save_as=upload_path)
        except Exception as e:
            raise Exception(f"Failed to create docx: {str(e)}")
        output = buf.getvalue()

    new_key = make_new_key(docket, common_filename)
    try:
        s3_client.upload_file(upload_path, bucket, new_key)
        logger.info("## DONE")
        logger.info(output)
    except ClientError as e:
        logger.error(e)
        return False
    return True


def make_new_key(docket, common_filename):
    return f"converted/{docket} {common_filename}.docx"


def get_docket(filename):
    path = Path(filename)
    match = valid_docket_type1.search(path.stem) or valid_docket_type2.search(path.stem)
    if match:
        return match.group(0).upper()
    else:
        raise Exception(f"Could not find a valid docket number in: {path.stem}")
