import re
from pathlib import Path
import tscribe


base_dir = Path(".")

converted_dir = base_dir / "converted"
unconverted_dir = base_dir / "unconverted"
valid_docket_type1 = re.compile(r"P\d+-\w{2}\d{2}", flags=re.IGNORECASE)
valid_docket_type2 = re.compile(r"\w{3}-\d{3}\w{2}\d{2}")


def main():
    paths = get_filepaths()
    if not paths:
        print("No files found to convert!")
        return

    print("Converting files......")
    for path in paths:
        docket = get_docket(path)
        if not docket:
            continue
        create_dir(docket)
        transcribe(path, docket)
        move_json(path, docket)

    print("Done!")


def move_json(old_path, docket):
    target = converted_dir / docket / old_path.name
    old_path.rename(target)


def transcribe(path, docket):
    tscribe.write(
        str(path), save_as=f"converted/{docket}/{docket} Disclosure Call.docx"
    )


def create_dir(docket):
    dir_path = converted_dir / docket
    dir_path.mkdir()


def get_docket(path):
    # The final path component, without its suffix
    match = valid_docket_type1.search(path.stem) or valid_docket_type2.search(path.stem)
    if match:
        return match.group(0).upper()


def get_filepaths() -> list:

    return [x for x in unconverted_dir.iterdir() if x.suffix == ".json"]
