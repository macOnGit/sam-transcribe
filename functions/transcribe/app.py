import logging
import json
import boto3
from pathlib import Path
import re
import os


transcribe = boto3.client("transcribe")
valid_docket_type1 = re.compile(r"P\d+-\w{2}\d{2}", flags=re.IGNORECASE)
valid_docket_type2 = re.compile(r"\w{3}-\d{3}\w{2}\d{2}")
logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):

    max_speakers = os.environ.get("MAX_SPEAKERS")
    if not max_speakers:
        raise Exception("Cannot find env MAX_SPEAKERS")

    logger.info("## EVENT")
    logger.info(json.dumps(event, indent=2))

    # filename includes directory path
    filename = event["Records"][0]["s3"]["object"]["key"]
    bucketname = event["Records"][0]["s3"]["bucket"]["name"]
    url = f"s3://{bucketname}/{filename}"
    # The final path component, without its suffix
    save_as_filename = get_docket(filename)
    # The suffix
    media_format = get_media_format(filename)

    response = transcribe.start_transcription_job(
        TranscriptionJobName=f"audiotojson-{save_as_filename}",
        LanguageCode="en-US",
        MediaFormat=media_format,
        Media={"MediaFileUri": url},
        Settings={
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": int(max_speakers),
        },
        OutputBucketName=bucketname,
        OutputKey=f"transcribed/{save_as_filename}.json",
    )

    logger.info("## RESPONSE")
    logger.info(response)


def get_docket(filename):
    path = Path(filename)
    match = valid_docket_type1.search(path.stem) or valid_docket_type2.search(path.stem)
    if match:
        return match.group(0).upper()
    else:
        raise Exception(f"Could not find a valid docket number in: {path.stem}")


def get_media_format(filename):
    path = Path(filename)
    try:
        return path.suffix.split(".")[1]
    except IndexError:
        raise Exception(f"Could not figure out media format from: {filename}")
