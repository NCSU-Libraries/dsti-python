#!/usr/bin/env python3
"""Copy the session notebooks into the built site, so the Download links work.

Quarto runs this after a full render (project: post-render in site/_quarto.yml).
It copies notebooks/*.ipynb into <output dir>/notebooks/. Quarto sets
QUARTO_PROJECT_OUTPUT_DIR; without it, the output dir is site/_site.

The files go only into the output. Copied into site/, Quarto would render the
.ipynb files as pages and rewrite the links.
"""
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "notebooks"


def output_dir() -> Path:
    env = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    if not env:
        return REPO / "site" / "_site"
    out = Path(env)
    # Quarto may give a path relative to the project (site/), where it runs scripts.
    return out if out.is_absolute() else (REPO / "site" / out).resolve()


def main() -> int:
    notebooks = sorted(SRC.glob("*.ipynb"))
    if not notebooks:
        print(f"copy_notebooks: no notebooks found in {SRC}", file=sys.stderr)
        return 1
    dest = output_dir() / "notebooks"
    dest.mkdir(parents=True, exist_ok=True)
    for nb in notebooks:
        shutil.copy2(nb, dest / nb.name)
        print(f"copy_notebooks: {nb.name} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
