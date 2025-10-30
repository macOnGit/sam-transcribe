from functions.convert import app
import pytest


@pytest.mark.parametrize("event", ["audio_transcribed"], indirect=True)
def test_gets_docket_from_filename(event):
    filename = event["Records"][0]["s3"]["object"]["key"]
    docket = app.get_docket(filename)
    assert docket == "P12345-US01"


def test_default_filename():
    filename = "somefile.mp3"
    docket = app.get_docket(filename)
    assert "Conversion-" in docket


def test_logs_warning_for_invalid_docket(caplog):
    filename = "invalid_filename.mp3"
    app.get_docket(filename)
    assert any("Docket not found in filename" in message for message in caplog.messages)


def test_raises_without_common_filename_env():
    with pytest.raises(Exception) as err:
        app.lambda_handler({}, {})
    assert "COMMON_FILENAME" in str(err.value)
