# sam-transcribe

An application which takes an uploaded audio file from one bucket and returns a docx file in another.

Steps:

1. An audio file is uploaded to _UploadBucket_ which causes _RunTranscriptionJob_ to a start transcription job.
2. The generated transcription placed in _DownloadBucket_ causes _CovertToDocx_ to run.
3. The new docx file is placed in _DownloadBucket_.

## Lambda Functions

Previous transcription job of same name will be deleted to avoid conflict

## S3 Buckets

- Bucket names must conform to below the expression which follows AWS S3 bucket naming [rules](https://stackoverflow.com/a/50484916)

`^(?!(^xn--|.+-s3alias$))^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$`

- Common File Name (e.g., "- Call transcript") must conform to the below expression which follows
  AWS S3 object naming
  [rules](https://stackoverflow.com/a/58713447) but without forward slashes and spaces are allowed

`^[ a-zA-Z0-9!_.*\'()-]+$`

**NOTE**: a file with the same key will overwrite the old in a bucket

## Testing

[local event](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-generate-event.html)

[mock testing](https://docs.getmoto.org/en/latest/index.html)

audio file and json file required in fixtures/ to run tests - use same docket number for both!

Invoke function locally using the command
`sam local invoke --event events/audio_uploaded.json RunTranscriptionJob`

Testing framework is [pytest](https://docs.pytest.org/en/stable/index.html) +
[pytest-order](https://pypi.org/project/pytest-order/)

## Useful Commands

Create a folder in the bucket using the command
`aws s3api put-object --bucket bucket-name --key folder-name/ --content-length 0`

Upload the application's artifacts to Amazon S3 and output a new template file
`sam package --output-template-file package.yml --s3-bucket <your-bucket-name>`

## Logging

[logging in lambda](https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html)

[logging in cloudformation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-loggingconfig.html)

## Sam Template

[anatomy](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html)
