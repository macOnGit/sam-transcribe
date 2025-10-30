from functions.transcribe import app
import pytest


@pytest.mark.parametrize("event", ["audio_uploaded"], indirect=True)
def test_gets_docket_from_filename(event):
    filename = event["Records"][0]["s3"]["object"]["key"]
    docket = app.get_docket(filename)
    assert docket == "P12345-US01"


def test_default_filename():
    filename = "something invalid"
    docket = app.get_docket(filename)
    assert "Transcription-" in docket


def test_logs_warning_for_invalid_docket(caplog):
    filename = "invalid_filename.mp3"
    app.get_docket(filename)
    assert any("Docket not found in filename" in message for message in caplog.messages)


@pytest.mark.parametrize("event", ["audio_uploaded"], indirect=True)
def test_gets_media_format(event):
    filename = event["Records"][0]["s3"]["object"]["key"]
    media_format = app.get_media_format(filename)
    assert media_format == "m4a"


def test_raises_when_media_format_missing():
    filename = "something invalid"
    with pytest.raises(Exception) as err:
        app.get_media_format(filename)
    assert "media format" in str(err.value)


def test_raises_without_max_speakers_env():
    with pytest.raises(Exception) as err:
        app.lambda_handler({}, {})
    assert "MAX_SPEAKERS" in str(err.value)
