from functions.convert import app
import pytest


@pytest.mark.parametrize("event", ["audio_transcribed"], indirect=True)
def test_gets_docket_from_filename(event):
    filename = event["Records"][0]["s3"]["object"]["key"]
    docket = app.get_docket(filename)
    assert docket == "P12345-US01"


def test_raises_without_tagline_env():
    with pytest.raises(Exception) as err:
        app.lambda_handler({}, {})
    assert "TAGLINE" in str(err.value)
