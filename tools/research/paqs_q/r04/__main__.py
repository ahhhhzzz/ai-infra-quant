"""Explicit offline experiment entry point; exclusive output directory required."""

import argparse
from pathlib import Path

from .study import run

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", type=Path, required=True)
parser.add_argument("--calendar-file", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
run(Path.cwd(), args.data_dir, args.calendar_file, args.output)
