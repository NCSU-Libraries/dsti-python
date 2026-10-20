#!/usr/bin/env python3
"""Rebuild the two ATUS data files used by the time-use activity.

    python3 tools/atus_data.py [--src DIR] [--out DIR]

Reads the DSTI team's files from --src and writes into --out (default: this repo's data/):

  atus_raw.csv      a straight copy of raw_ATUS_DSTI_from_tsv.csv. The original ATUS variable
                    names and numeric codes: the source of truth.
  atus_working.csv  working_ATUS_DSTI_from_tsv.csv with the Metropolitan labels mapped back to
                    ATUS codes (Metropolitan 1, Non-metropolitan 2, Not identified 3, Blank -1).
                    This is the file learners clean. It matches the spreadsheets track's Google
                    Sheet, where Metropolitan is also a code.

The working file is read and written with csv.reader and csv.writer (utf-8, newline="",
default minimal quoting), so it is not a byte copy: the quotes the team's export puts around
every text value are dropped where they aren't needed.

The mistakes in the working file (Sex and Education typos, the "NA" sleep values, the age of
150, the duplicate rows, the Case with two ages) are in the team's file already. This script
doesn't add or remove any. The two files are 2,000 respondents sampled from ATUS diary years
2003-2023 (American Time Use Survey, U.S. Bureau of Labor Statistics, via ICPSR study 36268).

Standard library only.
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = (
    "~/Library/CloudStorage/GoogleDrive-atezbas@ncsu.edu/Shared drives/"
    "Data Science Training Intensive/Training Content/Track Content/teaching dataset/output"
)
DEFAULT_OUT = ROOT / "data"

SRC_RAW = "raw_ATUS_DSTI_from_tsv.csv"
SRC_WORKING = "working_ATUS_DSTI_from_tsv.csv"
OUT_RAW = "atus_raw.csv"
OUT_WORKING = "atus_working.csv"

METRO_CODES = {"Metropolitan": "1", "Non-metropolitan": "2", "Not identified": "3", "Blank": "-1"}


def build_working(src_file: Path, out_file: Path):
    """Write the working file with Metropolitan labels turned back into codes."""
    with open(src_file, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    col = header.index("Metropolitan")
    for n, row in enumerate(rows[1:], start=2):
        assert len(row) == len(header), f"line {n}: {len(row)} fields, expected {len(header)}"
        assert row[col] in METRO_CODES, f"line {n}: unknown Metropolitan value {row[col]!r}"
        row[col] = METRO_CODES[row[col]]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)  # LF, as git stores it
    return len(rows) - 1, len(header)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=DEFAULT_SRC, help="the team's output folder (synced shared drive)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="where to write the two files (default: data/)")
    args = ap.parse_args()
    src, out = Path(args.src).expanduser(), Path(args.out).expanduser()
    for name in (SRC_RAW, SRC_WORKING):
        if not (src / name).is_file():
            sys.exit(f"missing {src / name}. Is the shared drive synced? Pass --src to point elsewhere.")
    out.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(src / SRC_RAW, out / OUT_RAW)
    n_rows, n_cols = build_working(src / SRC_WORKING, out / OUT_WORKING)
    with open(out / OUT_RAW, newline="", encoding="utf-8") as f:
        n_raw = sum(1 for _ in csv.reader(f)) - 1
    print(f"Wrote {out / OUT_RAW} ({n_raw} rows)")
    print(f"Wrote {out / OUT_WORKING} ({n_rows} rows, {n_cols} columns)")


if __name__ == "__main__":
    main()
