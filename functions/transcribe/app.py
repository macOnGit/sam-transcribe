import logging
import json
import time
import boto3
from pathlib import Path
from urllib.parse import unquote_plus
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
    outputbucketname = os.environ.get("DOWNLOAD_BUCKET_NAME")
    if not outputbucketname:
        raise Exception("Cannot find env DOWNLOAD_BUCKET_NAME")

    logger.info("## EVENT")
    logger.info(json.dumps(event, indent=2))

    # key includes directory path
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    bucketname = event["Records"][0]["s3"]["bucket"]["name"]
    url = f"s3://{bucketname}/{key}"
    # The final path component, without its suffix
    save_as_filename = get_docket(key)
    # The suffix
    media_format = get_media_format(key)
    transcription_job_name = f"audiotojson-{save_as_filename}"

    del_previous_job(transcription_job_name)
    wait_for_previous_job_to_be_del(transcription_job_name)

    response = transcribe.start_transcription_job(
        TranscriptionJobName=transcription_job_name,
        LanguageCode="en-US",
        MediaFormat=media_format,
        Media={"MediaFileUri": url},
        Settings={
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": int(max_speakers),
        },
        OutputBucketName=outputbucketname,
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
        return f"Transcription-{int(time.time())}"


def del_previous_job(transcription_job_name):
    try:
        transcribe.delete_transcription_job(TranscriptionJobName=transcription_job_name)
        logger.info(f"Deleted previous transcription job: {transcription_job_name}")
    except Exception:
        pass


def wait_for_previous_job_to_be_del(transcription_job_name):
    MAX_WAIT = 80
    start_time = time.time()

    while True:
        try:
            job = transcribe.get_transcription_job(
                TranscriptionJobName=transcription_job_name
            )
            if job:
                logger.info(f"Previous job {transcription_job_name} still exists")
        except (
            transcribe.exceptions.NotFoundException,
            transcribe.exceptions.BadRequestException,
        ):
            return
        if time.time() - start_time > MAX_WAIT:
            raise Exception(f"Could not delete previous job: {transcription_job_name}")

        time.sleep(10)


def get_media_format(filename):
    path = Path(filename)
    try:
        return path.suffix.split(".")[1]
    except IndexError:
        raise Exception(f"Could not figure out media format from: {filename}")
