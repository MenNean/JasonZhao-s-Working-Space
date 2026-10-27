from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search BI digital employee reference files."
    )
    parser.add_argument("query", help="Case-insensitive text to search for.")
    parser.add_argument(
        "--limit", type=int, default=80, help="Maximum matching lines to print."
    )
    args = parser.parse_args()

    query = args.query.lower()
    count = 0
    for path in sorted(REFERENCES.iterdir()):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if query in line.lower():
                print(f"{path.name}:{lineno}: {line}")
                count += 1
                if count >= args.limit:
                    return


if __name__ == "__main__":
    main()
