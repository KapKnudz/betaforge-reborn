"""Attach a bounded editorial memo to a structured saved view under ignored data/."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from betaforge.saved_view import MAX_BYTES, _json, attach_reader_memo, checked_path, load_saved_view


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("view", "memo", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    try:
        output = checked_path(args.output)
        private = Path(__file__).resolve().parents[1] / "data"
        if (not output.is_relative_to(private) or output.is_relative_to(private / "bf-borsdata-research")
                or output.suffix != ".json"):
            raise ValueError("Output must be a new JSON file under the ignored data/ directory")
        view = attach_reader_memo(load_saved_view(args.view), _json(args.memo))
        body = json.dumps(view, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if len(body.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Saved view exceeds 16 MiB")
        output.parent.mkdir(parents=True, exist_ok=True)
        checked_path(output)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(body)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, "Reader-memo attachment failed: " + str(error) + "\n")
    print("Saved reader-memo view: " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
