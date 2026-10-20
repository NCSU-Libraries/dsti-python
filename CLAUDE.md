# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Materials for **Introduction to Programming with Python**, a 2.5-hour NC State University Libraries Data Science Services session
taught by Alp Tezbasaran at the Data Science Training Intensive (DSTI).

- **When and where:** Tuesday 2026-10-20, DSTI Day 2's Python track, East Learning Lab A. Check-in is at 8:30, the
  slot runs 9:00–11:30, and the all-track wrap-up is at 11:30 in the same room. The plan uses 130 of the 150 minutes;
  the home page shows 11:10–11:30 as practice, questions and install help. Facts live in `event` in `site/_variables.yml`.
- **Lesson plan:** `~/Desktop/projects/dss/dsti/python/Lesson_Plan_Blended_Accelerated.md`. It's private and never goes
  in this repo. It times every segment; the notebook's sections 1–10 are its Sections 4–13.
- **Contacts:** workshop questions go to lib-datascienceservices@ncsu.edu. Setup and access help goes to
  go.ncsu.edu/getdatahelp.

**Design (changed 2026-10-20: local first, Colab as the backup):** attendees install Python with uv, make a `dss-python`
project, run `uv add jupyterlab matplotlib`, download the learner notebook from the site, and work in JupyterLab on their
own laptop. A checkpoint at 0:28 (learners see "around 9:30") sends anyone whose bar plot cell won't run to Google Colab,
the backup, with the same notebook. Conda (conda-forge only) is a documented alternative to uv on the Setup page, not
demoed. One notebook pair: a learner notebook and a filled one, condensed from the getting-started-with-python Basics and
Loops and Functions notebooks. The deck summarizes each segment; it never reproduces notebook cells.

`uv add jupyterlab matplotlib` puts the server, the kernel and matplotlib in the project's one `.venv`. uv's own docs
prefer `uv run --with jupyter`; one environment is deliberately simpler for beginners, and `uv run jupyter lab` is the
whole restart story.

## Layout

| Path | Contents |
| --- | --- |
| `notebooks/introduction-to-programming-with-python.ipynb` | Learner notebook: blank code under comment scaffolds |
| `notebooks/introduction-to-programming-with-python-solutions.ipynb` | Filled notebook: every exercise answered |
| `tools/build_notebooks.py` | Generates both notebooks from getting-started-with-python at pinned commit `9b288fa` |
| `notebooks/activity-*.ipynb` | Follow-along activities for after the session, learner and `-solutions` versions |
| `tools/build_activities.py` | Generates the activity notebooks from one module per activity in `tools/activities/` (auto-discovered) |
| `data/` | The activities' CSVs. `atus_*.csv` come from the DSTI teaching dataset via `tools/atus_data.py` |
| `data/cafe_sales.csv` | The café activity's data: synthetic, copied byte for byte from `agentic-coding-with-claude/starters/cafe/cafe_sales.csv` (CC BY 4.0). Its planted problems are on purpose; don't clean the file |
| `site/activities/` | One page per activity: finish line, setup, steps, check numbers, data dictionary |
| `tools/copy_notebooks.py` | Quarto post-render step: copies `notebooks/*.ipynb` and `data/*.csv` into `site/_site/` for the Download links |
| `site/` | Quarto website plus the reveal.js deck (`site/slides/index.qmd`) |
| `site/_variables.yml` | Facts used on several pages and in the deck: event, links, downloads, the conda command, Python and uv versions |
| `tools/check_links.py` | Checks every link and image in `site/_site` (`--web` also requests external URLs) |
| `tools/shoot.mjs` | Headless Chrome screenshots of pages or slides. Gives a `slide` index in reading order |

## Commands

```bash
Q=/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto   # Quarto isn't on PATH on this Mac
python3 tools/build_notebooks.py --src ~/Desktop/getting-started-with-python   # regenerate both notebooks
python3 tools/build_activities.py                                      # regenerate the activity notebooks (--check: fail if stale)
python3 tools/atus_data.py                                             # rebuild data/atus_*.csv from the DSTI shared drive
$Q render site                                                         # full build into site/_site (+ notebooks/ via post-render)
$Q render site/slides/index.qmd                                        # the deck only
python3 tools/check_links.py                                           # after a render
# Run the filled notebook top to bottom on Colab's Python; only cells tagged raises-exception may raise
uv run --python 3.13 --with jupyter --with matplotlib jupyter nbconvert --to notebook --execute --stdout notebooks/introduction-to-programming-with-python-solutions.ipynb > /dev/null
```

The Pages workflow (`.github/workflows/deploy-pages.yml`) runs `quarto render site` with Quarto 1.10.18. Only Alp
pushes.

## Keeping things consistent

- **The notebooks are generated.** Change them by editing the manifest in `tools/build_notebooks.py` and re-running
  it. Hand edits to the `.ipynb` files are overwritten on the next build. The activity notebooks are generated too:
  edit `tools/activities/<name>.py` and run `tools/build_activities.py`.
- **Each activity's numbers are in three places**: its notebook's *Check your numbers*, its page's *Check your
  numbers*, and the notebook's own outputs. They were checked with Polars 2.0.0 (`activities.*.polars` in
  `_variables.yml`). Change the data or the pipeline, re-run the filled notebook, and update both tables.
- **The time-use activity shares its data with the DSTI spreadsheets track.** `data/atus_working.csv` is the team's
  `working_ATUS_DSTI_from_tsv.csv` with Metropolitan put back to ATUS codes, to match their Google Sheet. Its
  mistakes are planted on purpose (see `DSTI_dataset-spec.md` on the shared drive); don't clean them. The source is
  ICPSR study 36268 (BLS ATUS).
- **Learner and filled are paired by cell id**: same cells, same order. The build script asserts it, and asserts that
  the learner never has code the filled notebook lacks (exempt: the `my_info = []` scaffold and the four fix-the-error
  cells, whose learner code is deliberately broken).
- **Section names appear in four places**: the notebook, the deck, the site pages, and the lesson plan. Rename one,
  rename all.
- **The go link is on the slides, the QR code and the pages.** If it changes, update `go` in `site/_variables.yml`,
  the deck's `footer:` in `site/slides/index.qmd` (YAML can't use `var`), and regenerate `site/images/qr-session.svg`.
- **The AI workshop list is in two places**: the home page's "More AI workshops from us" and the deck slide of the
  same name. Titles drop the "Data Science Special Topics:" prefix. Change both together.
- **The deck sets `from: markdown-smart`** so quotes in commands stay straight; keep it, or `"irm …"` turns curly.
- **`uv init` needs `--no-package`.** Since uv 0.13, a plain `uv init` makes a packaged project (`src/`, a build
  backend, a build step in `uv add`). The flag keeps the simple `main.py` project the Setup page describes, and it works
  on older uv too. It appears on the Setup page, the cheat sheet, the deck and the video's scenes.
- **Python version:** `uv init --python` on the Setup page and `python=` in `conda.create` must match Colab's Python
  (`python` in `site/_variables.yml`). Check with `!python --version` in Colab before each run of the session.
- **The learner flow is in five places**: the Setup page, the deck's install and JupyterLab sections, the cheat sheet's
  commands table, the notebook's *Open this notebook again later*, and the lesson plan's Sections 2–3. Change them
  together, including the 9:30 checkpoint.

## Gotchas

- **The Colab links only work once the repo is public on GitHub** and the notebooks are pushed.
- **Quarto smartens `{{< var >}}` values**, even inside code blocks: a bare `--` becomes an en dash. Escape hyphens in
  `_variables.yml` (`\\-\\-`), as `conda.create` does, and grep the rendered HTML after changing one.
- **Download links** to `notebooks/*.ipynb` carry `download` and `data-noresolveinput`; without the latter Quarto warns
  "Unable to resolve link target", because the files only exist after post-render. Navbar items can't carry
  `download`, so the navbar links to the Setup page's `#notebook` step instead.
- **Windows PowerShell's `curl` is an alias** for `Invoke-WebRequest`. The Setup page's optional terminal download uses
  `curl.exe`.
- **The home page checklist stores its state under the localStorage key `dsti-python-finish-line`.** Every
  ncsu-libraries.github.io site shares one origin, so a generic key would collide with other workshop sites.
- **Quarto slides:**
  - Quarto gives level-1 (`#`) section slides the class `title-slide`, and `ncsu.scss` paints that white. The
    `.divider` rules in `site/theme/slides.scss` keep them red, so every `#` section needs `{.divider}`.
  - Slides nest under `#` sections, so `Reveal.slide(n)` doesn't step through them in order. `shoot.mjs` uses
    `Reveal.getSlides()` instead.
- The theme files and the DSS images were copied from `agentic-coding-with-claude`. Keep them in step if that design
  changes.
