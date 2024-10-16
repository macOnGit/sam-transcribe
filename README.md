# sam-transcribe

## Buckets

Bucket name must conform to AWS S3 bucket naming [rules](https://stackoverflow.com/a/50484916)

`^(?!(^xn--|.+-s3alias$))^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$`

Common File Name (e.g., "- Call transcript") must conform to AWS S3 object naming
[rules](https://stackoverflow.com/a/58713447) but without forward slashes and spaces are allowed

`^[ a-zA-Z0-9!_.*\'()-]+$`

## Testing

[local event](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-generate-event.html)

[mock testing](https://docs.getmoto.org/en/latest/index.html)

audio file and json file required in fixtures/ to run tests - use same docket number for both!

Invoke function locally using the command
`sam local invoke --event events/audio_uploaded.json RunTranscriptionJob`

## useful commands

Create a folder in the bucket using the command
`aws s3api put-object --bucket bucket-name --key folder-name/ --content-length 0`

## logging

[logging in lambda](https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html)

[logging in cloudformation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-loggingconfig.html)

## sam template

[anatomy](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html)
