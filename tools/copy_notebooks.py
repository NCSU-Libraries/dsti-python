#!/usr/bin/env python3
"""Copy the notebooks and the activity data into the built site, so the Download links and the data URLs work.

Quarto runs this after a full render (project: post-render in site/_quarto.yml).
It copies two things into the output dir (Quarto sets QUARTO_PROJECT_OUTPUT_DIR;
without it, the output dir is site/_site):

- notebooks/*.ipynb -> <output dir>/notebooks/ (the session notebooks and the activity notebooks)
- data/*.csv        -> <output dir>/data/ (the time-use activity's files; its notebook downloads them from the site)

The files go only into the output. Copied into site/, Quarto would render the
.ipynb files as pages and rewrite the links.
"""
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# (source folder, file pattern, folder inside the output)
COPIES = [
    (REPO / "notebooks", "*.ipynb", "notebooks"),
    (REPO / "data", "*.csv", "data"),
]


def output_dir() -> Path:
    env = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    if not env:
        return REPO / "site" / "_site"
    out = Path(env)
    # Quarto may give a path relative to the project (site/), where it runs scripts.
    return out if out.is_absolute() else (REPO / "site" / out).resolve()


def main() -> int:
    out = output_dir()
    for src, pattern, name in COPIES:
        files = sorted(src.glob(pattern))
        if not files:
            print(f"copy_notebooks: no {pattern} files found in {src}", file=sys.stderr)
            return 1
        dest = out / name
        dest.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, dest / f.name)
            print(f"copy_notebooks: {f.name} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
