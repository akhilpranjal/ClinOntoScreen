"""Export only aggregate, paper-safe result files from a notebook run."""
from __future__ import annotations

import argparse
from pathlib import Path

from src.clinontoscreen.reporting import export_public_results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    copied = export_public_results(args.source, args.destination)
    print("Exported:", ", ".join(str(path) for path in copied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
