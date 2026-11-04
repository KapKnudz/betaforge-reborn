"""Export a frozen structured run or legacy reviewed analysis to ignored data/."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from betaforge.saved_view import MAX_BYTES, build_saved_view, checked_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", help="Required for legacy runs; omit for structured analysis.json runs")
    for name in ("run", "packet", "company", "ticker", "id", "method", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    try:
        output = checked_path(args.output)
        private = Path(__file__).resolve().parents[1] / "data"
        if (not output.is_relative_to(private) or output.is_relative_to(private / "bf-borsdata-research")
                or output.suffix != ".json"):
            raise ValueError("Output must be a new JSON file under the ignored data/ directory")
        view = build_saved_view(args.review, args.run, args.packet, args.company, args.ticker, args.id, args.method)
        body = json.dumps(view, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if len(body.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Saved view exceeds 16 MiB")
        output.parent.mkdir(parents=True, exist_ok=True)
        checked_path(output)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(body)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, "Export failed: " + str(error) + "\n")
    print("Saved display export: " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
