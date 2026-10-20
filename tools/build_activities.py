#!/usr/bin/env python3
"""Build the learner and filled notebooks for the follow-along data activities.

    python3 tools/build_activities.py [--check] [SLUG ...]

Each activity is one module in tools/activities/ (files starting with "_" are skipped). This
script discovers them by scanning tools/activities/*.py, so adding an activity means adding one
file and never editing this one. A module defines:

    SLUG            "time-use"; names the outputs and the activity page
    ID_PREFIX       "tu"; every cell id is "<ID_PREFIX>-<cell slug>", for example "tu-read-csv"
    TITLE_LEARNER   the learner notebook's first (markdown) cell
    TITLE_FILLED    the filled notebook's first cell; the only markdown that may differ
    CELLS           the other cells, in order, built with md()/code() from build_notebooks.py

The title becomes cell "<ID_PREFIX>-title", so CELLS doesn't include one. For each module this
writes notebooks/activity-<SLUG>.ipynb (learner) and notebooks/activity-<SLUG>-solutions.ipynb
(filled) from CELLS, using the helpers in build_notebooks.py, and asserts that:

  - both versions have the same ids, types and order
  - markdown is identical except the title
  - every non-comment, non-blank learner code line appears in the filled cell
  - ids are unique, start with the prefix and match ^[A-Za-z0-9_-]{1,64}$
  - the two titles link to each other (the Colab URLs for this SLUG)

With --check nothing is written: the notebooks are built in memory and compared with the files
on disk, and the exit status is 1 if any is stale. Running the build twice changes nothing.
Standard library only. Edit the notebooks only through this script and the activity modules.
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# Reused from the session builder, not copied: the cell objects, the cell/notebook JSON and the writer.
from build_notebooks import COLAB, ROOT, New, dump, make_cell, notebook, outline, src_text  # noqa: E402

ACTIVITIES_DIR = TOOLS / "activities"
REQUIRED = ("SLUG", "ID_PREFIX", "TITLE_LEARNER", "TITLE_FILLED", "CELLS")


class Activity:
    """One activity module, loaded and checked for the names the builder needs."""

    def __init__(self, path: Path):
        self.path = path
        spec = importlib.util.spec_from_file_location(f"activity_{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in REQUIRED:
            assert hasattr(mod, name), f"{path.name}: missing {name}"
        self.slug, self.prefix = mod.SLUG, mod.ID_PREFIX
        self.title_learner, self.title_filled = mod.TITLE_LEARNER, mod.TITLE_FILLED
        self.cells = list(mod.CELLS)
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", self.slug), f"{path.name}: bad SLUG {self.slug!r}"
        assert re.fullmatch(r"[a-z0-9]{1,8}", self.prefix), f"{path.name}: bad ID_PREFIX {self.prefix!r}"
        for e in self.cells:
            assert isinstance(e, New), f"{path.name}: CELLS entries come from md()/code()/New(), got {e!r}"
            assert e.slug != "title", f"{path.name}: the title comes from TITLE_LEARNER/TITLE_FILLED, not CELLS"

    @property
    def out_learner(self):
        return ROOT / "notebooks" / f"activity-{self.slug}.ipynb"

    @property
    def out_filled(self):
        return ROOT / "notebooks" / f"activity-{self.slug}-solutions.ipynb"

    @property
    def url_learner(self):
        return f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{self.slug}.ipynb"

    @property
    def url_filled(self):
        return f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{self.slug}-solutions.ipynb"

    def entries(self):
        """(cell id, entry) in output order, the title first."""
        title = New("title", "markdown", self.title_learner, filled=self.title_filled)
        return [(f"{self.prefix}-{e.slug}", e) for e in [title] + self.cells]


def discover():
    """Every activity module in tools/activities/, in file-name order, keyed by SLUG."""
    found = {}
    prefixes = {}
    for path in sorted(ACTIVITIES_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        act = Activity(path)
        assert act.slug not in found, f"{path.name}: SLUG {act.slug!r} is also used by {found[act.slug].path.name}"
        assert act.prefix not in prefixes, f"{path.name}: ID_PREFIX {act.prefix!r} is also used by {prefixes[act.prefix]}"
        found[act.slug] = act
        prefixes[act.prefix] = path.name
    return found


# ----------------------------------------------------------------------------
# Build and check
# ----------------------------------------------------------------------------

def build(act: Activity):
    learner, filled = [], []
    for cid, entry in act.entries():
        lt, ltext, ltags = entry.build(None, filled=False)
        ft, ftext, ftags = entry.build(None, filled=True)
        assert lt == ft, f"{cid}: cell types differ between versions"
        learner.append(make_cell(cid, lt, ltext, ltags))
        filled.append(make_cell(cid, ft, ftext, ftags))
    return learner, filled


def code_lines(cell):
    """The non-blank, non-comment lines of a code cell."""
    return [l for l in src_text(cell).splitlines() if l.strip() and not l.strip().startswith("#")]


def check(act: Activity, learner, filled):
    # 1. same count, ids, types, order
    assert len(learner) == len(filled), "cell counts differ"
    for a, b in zip(learner, filled):
        assert a["id"] == b["id"], f"ids differ: {a['id']} / {b['id']}"
        assert a["cell_type"] == b["cell_type"], f"types differ at {a['id']}"
    # 4. ids unique, well formed, prefixed
    ids = [c["id"] for c in learner]
    assert len(set(ids)) == len(ids), "duplicate ids: " + str(sorted({i for i in ids if ids.count(i) > 1}))
    for i in ids:
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", i), f"bad id {i!r}"
        assert i.startswith(act.prefix + "-"), f"id {i!r} doesn't start with {act.prefix}-"
    title_id = f"{act.prefix}-title"
    assert ids[0] == title_id and learner[0]["cell_type"] == "markdown", "the first cell should be the markdown title"
    for a, b in zip(learner, filled):
        if a["cell_type"] == "markdown":
            # 2. markdown identical except the title
            if a["id"] != title_id:
                assert src_text(a) == src_text(b), f"markdown differs at {a['id']}"
        else:
            # 3. every non-comment, non-blank learner line appears in the filled cell
            f_lines = {l.rstrip() for l in src_text(b).splitlines()}
            for line in code_lines(a):
                assert line.rstrip() in f_lines, f"{a['id']}: learner line missing from filled cell: {line!r}"
            assert code_lines(b), f"{a['id']}: the filled cell has no code"
    # the titles link to each other and differ
    assert src_text(learner[0]).startswith("# ") and src_text(filled[0]).startswith("# "), "titles need a # heading"
    assert src_text(learner[0]) != src_text(filled[0]), "the two titles are identical"
    assert act.url_filled in src_text(learner[0]), f"learner title doesn't link to {act.url_filled}"
    assert act.url_learner in src_text(filled[0]), f"filled title doesn't link to {act.url_learner}"
    # house style and beginner-friendly code
    for nb in (learner, filled):
        for c in nb:
            t = src_text(c)
            assert "\u2014" not in t, f"em dash in {c['id']}"
            assert not re.search(r"(?<!\d)–|–(?!\d)", t), f"en dash outside a number range in {c['id']}"
            assert c["metadata"] == {}, f"unexpected metadata in {c['id']}"
            if c["cell_type"] == "code":
                assert c["outputs"] == [] and c["execution_count"] is None, c["id"]
                for line in code_lines(c):
                    assert "+=" not in line, f"+= in {c['id']}: {line!r}"
                    assert not re.search(r"[\[{(][^\]})\n]*\bfor\b[^\]})\n]*\bin\b", line), (
                        f"comprehension in {c['id']}: {line!r}")


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

def rel(path: Path):
    return path.relative_to(ROOT)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slugs", nargs="*", metavar="SLUG", help="activities to build (default: all in tools/activities/)")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; exit 1 if a notebook on disk differs from what the build produces")
    args = ap.parse_args()

    found = discover()
    assert found, f"no activity modules in {ACTIVITIES_DIR}"
    unknown = [s for s in args.slugs if s not in found]
    assert not unknown, f"unknown activity {unknown}; have {sorted(found)}"
    chosen = [found[s] for s in (args.slugs or found)]

    stale = []
    for act in chosen:
        learner, filled = build(act)
        check(act, learner, filled)
        for path, cells in ((act.out_learner, learner), (act.out_filled, filled)):
            text = dump(notebook(cells))
            if args.check:
                if not path.exists() or path.read_bytes() != text.encode("utf-8"):
                    stale.append(rel(path))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                print(f"Wrote {rel(path)} ({len(cells)} cells)")
        print(f"{act.slug}: assertions passed.")
        if not args.check:
            print("\nTable of contents:")
            for line in outline(learner):
                print(line)
            print()
    if args.check:
        if stale:
            sys.exit("stale (run python3 tools/build_activities.py): " + ", ".join(str(p) for p in stale))
        print("Up to date: " + ", ".join(a.slug for a in chosen))


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        sys.exit(f"build failed: {e}")
