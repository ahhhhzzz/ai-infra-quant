"""Explicit local H1 JSON evaluation, no acquisition on the ordinary path."""

import argparse
from datetime import datetime
from pathlib import Path

from ..io import read_dataset
from ..types import canonical
from .engine import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["evaluate"])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--cutoff", type=datetime.fromisoformat, required=True)
    args = parser.parse_args()
    print(canonical(evaluate(read_dataset(args.input), args.cutoff).document()))


if __name__ == "__main__":
    main()
