# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Materials for **Introduction to Programming with Python**, a 2-hour NC State University Libraries Data Science Services session
taught by Alp Tezbasaran at the Data Science Training Intensive (DSTI).

- **When and where:** Tuesday 2026-10-20, DSTI Day 2's Python track, East Learning Lab A. Check-in is at 8:30, the
  slot runs 9:00–11:30, and the all-track wrap-up is at 11:30 in the same room. The plan uses 120 of the 150 minutes;
  the home page shows 11:00–11:30 as practice and questions. Facts live in `event` in `site/_variables.yml`.
- **Lesson plan:** `~/Desktop/projects/dss/dsti/python/Lesson_Plan_Blended_Accelerated.md`. It's private and never goes
  in this repo. It times every segment; the notebook's sections 1–10 are its Sections 4–13.
- **Contacts:** workshop questions go to lib-datascienceservices@ncsu.edu. Setup and access help goes to
  go.ncsu.edu/getdatahelp.

**Design (agreed 2026-10-19):** install Python with uv at the start, hard time-boxed to 0:17, then everything in Google
Colab from one notebook pair: a learner notebook and a filled one. Both are condensed from the getting-started-with-python
Basics and Loops and Functions notebooks. The deck summarizes each segment; it never reproduces notebook cells.

## Layout

| Path | Contents |
| --- | --- |
| `notebooks/introduction-to-programming-with-python.ipynb` | Learner notebook: blank code under comment scaffolds |
| `notebooks/introduction-to-programming-with-python-solutions.ipynb` | Filled notebook: every exercise answered |
| `tools/build_notebooks.py` | Generates both notebooks from getting-started-with-python at pinned commit `9b288fa` |
| `site/` | Quarto website plus the reveal.js deck (`site/slides/index.qmd`) |
| `site/_variables.yml` | Facts used on several pages and in the deck: event, links, Python and uv versions |
| `tools/check_links.py` | Checks every link and image in `site/_site` (`--web` also requests external URLs) |
| `tools/shoot.mjs` | Headless Chrome screenshots of pages or slides. Gives a `slide` index in reading order |

## Commands

```bash
Q=/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto   # Quarto isn't on PATH on this Mac
python3 tools/build_notebooks.py --src ~/Desktop/getting-started-with-python   # regenerate both notebooks
$Q render site                                                         # full build into site/_site
$Q render site/slides/index.qmd                                        # the deck only
python3 tools/check_links.py                                           # after a render
# Run the filled notebook top to bottom on Colab's Python; only cells tagged raises-exception may raise
uv run --python 3.13 --with jupyter --with matplotlib jupyter nbconvert --to notebook --execute --stdout notebooks/introduction-to-programming-with-python-solutions.ipynb > /dev/null
```

The Pages workflow (`.github/workflows/deploy-pages.yml`) runs `quarto render site` with Quarto 1.10.18. Only Alp
pushes.

## Keeping things consistent

- **The notebooks are generated.** Change them by editing the manifest in `tools/build_notebooks.py` and re-running
  it. Hand edits to the `.ipynb` files are overwritten on the next build.
- **Learner and filled are paired by cell id**: same cells, same order. The build script asserts it, and asserts that
  the learner never has code the filled notebook lacks (exempt: the `my_info = []` scaffold and the four fix-the-error
  cells, whose learner code is deliberately broken).
- **Section names appear in four places**: the notebook, the deck, the site pages, and the lesson plan. Rename one,
  rename all.
- **The go link is on the slides, the QR code and the pages.** If it changes, update `go` in `site/_variables.yml`,
  the deck's `footer:` in `site/slides/index.qmd` (YAML can't use `var`), and regenerate `site/images/qr-session.svg`.
- **The deck sets `from: markdown-smart`** so quotes in commands stay straight; keep it, or `"irm …"` turns curly.
- **Python version:** `uv init --python` on the Setup page must match Colab's Python (`python` in
  `site/_variables.yml`). Check with `!python --version` in Colab before each run of the session.

## Gotchas

- **The Colab links only work once the repo is public on GitHub** and the notebooks are pushed.
- **The home page checklist stores its state under the localStorage key `dsti-python-finish-line`.** Every
  ncsu-libraries.github.io site shares one origin, so a generic key would collide with other workshop sites.
- **Quarto slides:**
  - Quarto gives level-1 (`#`) section slides the class `title-slide`, and `ncsu.scss` paints that white. The
    `.divider` rules in `site/theme/slides.scss` keep them red, so every `#` section needs `{.divider}`.
  - Slides nest under `#` sections, so `Reveal.slide(n)` doesn't step through them in order. `shoot.mjs` uses
    `Reveal.getSlides()` instead.
- The theme files and the DSS images were copied from `agentic-coding-with-claude`. Keep them in step if that design
  changes.
