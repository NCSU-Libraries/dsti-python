#!/usr/bin/env python3
"""Build the learner and filled notebooks for the Accelerated Intro to Python session.

    python3 tools/build_notebooks.py [--src PATH]

Writes notebooks/accelerated-intro.ipynb (learner) and
notebooks/accelerated-intro-solutions.ipynb (filled) from one ordered manifest.

Source cells are read from the getting-started-with-python repo at a pinned commit
(`git show <commit>:<path>`), so later edits in that repo's working tree never leak in.
Standard library only.

Edit the notebooks only through this script. Hand edits get overwritten.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

COMMIT = "9b288fa"
DEFAULT_SRC = "~/Desktop/getting-started-with-python"
ROOT = Path(__file__).resolve().parent.parent
OUT_LEARNER = ROOT / "notebooks" / "accelerated-intro.ipynb"
OUT_FILLED = ROOT / "notebooks" / "accelerated-intro-solutions.ipynb"

SOURCES = {
    "B": (
        "workshops/basics/basics.ipynb",
        "workshops/basics/basics-solutions.ipynb",
    ),
    "L": (
        "workshops/loops-and-functions/loops-and-functions.ipynb",
        "workshops/loops-and-functions/loops-and-functions-solutions.ipynb",
    ),
}

# URLs (kept in step with site/_variables.yml; checked against it below when present)
COLAB = "https://colab.research.google.com/github/"
URL_LEARNER = COLAB + "NCSU-Libraries/dsti-python/blob/main/notebooks/accelerated-intro.ipynb"
URL_FILLED = COLAB + "NCSU-Libraries/dsti-python/blob/main/notebooks/accelerated-intro-solutions.ipynb"
URL_BASICS = COLAB + "NCSU-Libraries/getting-started-with-python/blob/main/workshops/basics/basics.ipynb"
URL_BASICS_F = COLAB + "NCSU-Libraries/getting-started-with-python/blob/main/workshops/basics/basics-solutions.ipynb"
URL_LOOPS = COLAB + "NCSU-Libraries/getting-started-with-python/blob/main/workshops/loops-and-functions/loops-and-functions.ipynb"
URL_LOOPS_F = COLAB + "NCSU-Libraries/getting-started-with-python/blob/main/workshops/loops-and-functions/loops-and-functions-solutions.ipynb"
URL_EDA = COLAB + "NCSU-Libraries/getting-started-with-python/blob/main/workshops/exploratory-data-analysis/exploratory-data-analysis.ipynb"
URL_SITE = "https://ncsu-libraries.github.io/dsti-python/"
URL_EVAL = "https://go.ncsu.edu/dss-workshop-eval"
URL_HELP = "https://go.ncsu.edu/getdatahelp"

RAISES = ["raises-exception"]


# ----------------------------------------------------------------------------
# Source loading
# ----------------------------------------------------------------------------

def load_source(src: Path):
    """Return {'B': (learner_cells, filled_cells), 'L': (...)} from the pinned commit."""
    out = {}
    for key, paths in SOURCES.items():
        pair = []
        for p in paths:
            raw = subprocess.run(
                ["git", "-C", str(src), "show", f"{COMMIT}:{p}"],
                check=True, capture_output=True, text=True,
            ).stdout
            pair.append(json.loads(raw)["cells"])
        learner, filled = pair
        assert len(learner) == len(filled), f"{key}: cell counts differ"
        for i, (a, b) in enumerate(zip(learner, filled)):
            assert a["cell_type"] == b["cell_type"], f"{key}{i}: cell types differ"
        out[key] = (learner, filled)
    assert len(out["B"][0]) == 112, "B should have 112 cells"
    assert len(out["L"][0]) == 119, "L should have 119 cells"
    for a, b in zip(*out["B"]):
        assert a["id"] == b["id"], "B ids should match across learner and solutions"
    return out


def text_of(cell):
    s = cell["source"]
    return s if isinstance(s, str) else "".join(s)


def first_line(text):
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


# ----------------------------------------------------------------------------
# Edit helpers (all fail loudly if the target is missing or ambiguous)
# ----------------------------------------------------------------------------

def H(old, new):
    """Replace the one line equal to `old`. new=None drops the line."""
    def edit(text):
        lines = text.split("\n")
        hits = [i for i, l in enumerate(lines) if l.rstrip() == old]
        assert len(hits) == 1, f"line not found exactly once: {old!r} (found {len(hits)})"
        if new is None:
            del lines[hits[0]]
        else:
            lines[hits[0]] = new
        return "\n".join(lines)
    return edit


def R(old, new):
    """Replace a substring that must occur exactly once."""
    def edit(text):
        assert text.count(old) == 1, f"substring not found exactly once: {old!r} (found {text.count(old)})"
        return text.replace(old, new)
    return edit


def bold(old_heading_line):
    """Turn a `### Foo` line into `**Foo**`."""
    m = re.match(r"^#+\s+(.*)$", old_heading_line)
    assert m, old_heading_line
    return H(old_heading_line, f"**{m.group(1)}**")


# ----------------------------------------------------------------------------
# Manifest entries
# ----------------------------------------------------------------------------

class Copy:
    """A cell copied from a source notebook.

    expect   first non-empty line of the learner (student) cell
    fexpect  first non-empty line of the solutions cell, when it differs from `expect`
    same     "learner": the filled output uses the learner's text
    text     replacement text for both versions (applied before edits)
    ltext / ftext   replacement text for one version
    fadd     lines appended to the filled version's text
    pre      text put before both versions
    edits / ledits / fedits   edit functions for both / learner / filled
    tags     cell tags (both versions) ; ftags for the filled version only (None = same as tags)
    """

    def __init__(self, src, idx, expect, fexpect=None, same=None, text=None, ltext=None,
                 ftext=None, fadd=None, pre="", edits=(), ledits=(), fedits=(),
                 tags=None, ftags="same"):
        self.src, self.idx, self.expect, self.fexpect = src, idx, expect, fexpect
        self.same, self.text, self.ltext, self.ftext = same, text, ltext, ftext
        self.fadd, self.pre = fadd, pre
        self.edits, self.ledits, self.fedits = edits, ledits, fedits
        self.tags = tags
        self.ftags = tags if ftags == "same" else ftags

    @property
    def label(self):
        return f"{self.src}{self.idx}"

    def cell_id(self, src_cells):
        if self.src == "B":
            return src_cells["B"][0][self.idx]["id"]
        return f"lf-{self.idx:03d}"

    def build(self, src_cells, filled):
        learner_cells, filled_cells = src_cells[self.src]
        lc, fc = learner_cells[self.idx], filled_cells[self.idx]
        l_text, f_text = text_of(lc), text_of(fc)
        assert first_line(l_text) == self.expect, (
            f"{self.label}: guard failed.\n  expected: {self.expect!r}\n  found:    {first_line(l_text)!r}")
        if self.same != "learner":
            want = self.fexpect if self.fexpect is not None else self.expect
            assert first_line(f_text) == want, (
                f"{self.label} (solutions): guard failed.\n  expected: {want!r}\n  found:    {first_line(f_text)!r}")
        elif self.fexpect is not None:
            assert first_line(f_text) == self.fexpect, f"{self.label} (solutions): guard failed"
        if filled:
            base = l_text if self.same == "learner" else f_text
            override = self.ftext if self.ftext is not None else self.text
            extra = self.fedits
        else:
            base = l_text
            override = self.ltext if self.ltext is not None else self.text
            extra = self.ledits
        t = base if override is None else override
        if filled and self.fadd:
            t = t.rstrip("\n") + "\n" + self.fadd
        t = self.pre + t
        for e in list(self.edits) + list(extra):
            t = e(t)
        tags = self.ftags if filled else self.tags
        return lc["cell_type"], t, tags


class New:
    """A cell written for this notebook. `filled` defaults to `learner`;
    `fadd` appends lines to the learner text for the filled version."""

    def __init__(self, slug, cell_type, learner, filled=None, fadd=None, tags=None):
        self.slug, self.cell_type = slug, cell_type
        self.learner, self.filled, self.fadd, self.tags = learner, filled, fadd, tags

    label = property(lambda self: f"new-{self.slug}")

    def cell_id(self, src_cells):
        return f"new-{self.slug}"

    def build(self, src_cells, filled):
        if filled:
            if self.filled is not None:
                t = self.filled
            elif self.fadd:
                t = self.learner.rstrip("\n") + "\n" + self.fadd
            else:
                t = self.learner
        else:
            t = self.learner
        return self.cell_type, t, self.tags


def md(slug, text):
    return New(slug, "markdown", text)


def code(slug, learner, fadd=None, filled=None):
    return New(slug, "code", learner, filled=filled, fadd=fadd)


# ----------------------------------------------------------------------------
# Title and closing cells
# ----------------------------------------------------------------------------

OUTCOMES = """1. Install Python with uv
2. Understand the differences between Python and Jupyter/Google Colab
3. Navigate the Google Colab environment
4. Create variables
5. Use basic data types and data structures, such as lists and dictionaries
6. Use arithmetic, comparison, and logical operators
7. Write an if statement and a for loop
8. Use methods with dot notation
9. Write a user-defined function"""

CREDIT = ("Built from the Getting Started with Python workshops (Basics; Loops and Functions) "
          "by Alp Tezbasaran, with credit to Selene R. Schmittling.")

TITLE_LEARNER = f"""# Accelerated Intro to Python

Data Science Training Intensive · NC State University Libraries, Data Science Services

{CREDIT}

**First: click Copy to Drive** in the toolbar and work in the new "Copy of …" tab. Edits in this tab aren't saved.

This is the learner notebook: write the code under each comment, with the instructor. The [filled notebook]({URL_FILLED}) has every answer.

**Today you will:**

{OUTCOMES}

Colab's AI features stay off today. Workshop site: [{URL_SITE}]({URL_SITE})"""

TITLE_FILLED = f"""# Accelerated Intro to Python: Filled

Data Science Training Intensive · NC State University Libraries, Data Science Services

{CREDIT}

**First: click Copy to Drive** in the toolbar and work in the new "Copy of …" tab. Edits in this tab aren't saved.

This is the filled notebook: every exercise has an answer, so check your work here. During the session, work in the [learner notebook]({URL_LEARNER}).

**Today you will:**

{OUTCOMES}

Colab's AI features stay off today. Workshop site: [{URL_SITE}]({URL_SITE})"""

KEEP_GOING = f"""## Keep going

**The full workshops**

These cover what we skipped: dates and times, type conversion, while loops and files. Next in the series is exploratory data analysis (EDA) with Polars.

- Basics: [learner]({URL_BASICS}) · [filled]({URL_BASICS_F})
- Loops and Functions: [learner]({URL_LOOPS}) · [filled]({URL_LOOPS_F})
- [Exploratory Data Analysis]({URL_EDA})

**Run this notebook on your laptop**

1. In Colab, choose File → Download → Download .ipynb and save the file in your `dss-python` folder.
2. In a terminal, go to the folder: `cd dss-python`
3. Start JupyterLab: `uv run --with jupyter jupyter lab`
4. The plot in Part 1 needs matplotlib. Run `uv add matplotlib` once.

**Resources**

- [A Byte of Python](https://python.swaroopch.com/) is a great intro book and reference for Python
- [Official Python documentation and tutorials](https://docs.python.org/3/)
- [Real Python](https://realpython.com/) contains a lot of different tutorials at different levels
- [LinkedIn Learning](https://www.linkedin.com/learning/) is free with NC State accounts and contains several video series for learning Python
- [Dataquest](https://www.dataquest.io/) is a free then paid series of courses with an emphasis on data science

**Tell us how we did**

Please spend a minute on the evaluation survey: [go.ncsu.edu/dss-workshop-eval]({URL_EVAL})

**Get help**

Questions about this session or about programming in general: [go.ncsu.edu/getdatahelp]({URL_HELP})"""


# ----------------------------------------------------------------------------
# The manifest, in output order
# ----------------------------------------------------------------------------

MANIFEST = [
    # ---- Title ----------------------------------------------------------
    New("title", "markdown", TITLE_LEARNER, filled=TITLE_FILLED),

    # ---- Part 1 ---------------------------------------------------------
    md("part-1", "# Part 1: Python basics"),

    md("sec-1", "## 1. Python and Colab"),
    Copy("B", 7, "## Python vs. Jupyter: What's the Difference?",
         edits=[H("## Python vs. Jupyter: What's the Difference?",
                  "### Python vs. Jupyter: what's the difference?")]),
    Copy("B", 9, "### Jupyter Environment",
         edits=[H("### Jupyter Environment", "### The Jupyter environment"),
                bold("### Source / Notebook Pane"),
                bold("### Console / Terminal"),
                bold("### Variable Inspector"),
                bold("### Output")]),
    Copy("B", 8, "### Example: Creating a simple bar plot",
         edits=[H("### Example: Creating a simple bar plot", "### Example: a simple bar plot")]),
    Copy("B", 10, "# Let's create a simple bar plot with matplotlib"),
    md("note-import",
       "`import` loads a package. Colab has the common ones; on your laptop you'd run `uv add matplotlib`. "
       "Open the Variables panel ({x}): `counts` and `regions` are there."),

    md("sec-2", "## 2. Notebook basics"),
    Copy("B", 12, "## Notebooks & Scripts",
         edits=[H("## Notebooks & Scripts", "### Notebooks and scripts")]),
    Copy("B", 13, "### Code cells and writing Python code",
         edits=[bold("#### Running a code cell"), bold("#### Comments and code")]),
    Copy("B", 14, "Code contains instructions that are executed when you run them. These are examples of lines of code:"),
    Copy("B", 15, "print('This is a line of code')"),
    Copy("B", 16, "4 * 4"),
    Copy("B", 17, "**Try it yourself:** What is the output of running this cell?"),
    Copy("B", 18, "# 1 + 1"),
    Copy("B", 19, "By default, in Jupyter Notebooks and Google Colab the last line that produces a value in a code cell is printed. To print a value that is not at the end of a code cell use the `print()` function"),
    Copy("B", 20, "print('This string is printed using the print function')"),
    Copy("B", 23, "#### Finding Help in Colab",
         edits=[H("#### Finding Help in Colab", "### Finding help")]),
    Copy("B", 24, "# Run this cell to find out what the built-in Python function \"len\" does"),
    md("note-indent", "Indentation is part of Python's grammar. You'll see why with `if` in Part 2."),

    md("sec-3", "## 3. Variables and data types"),
    Copy("B", 27, "# Variables in Python",
         edits=[H("# Variables in Python", "### Variables"),
                R("digits (0-1)", "digits (0-9)"),
                R("They are important the building blocks", "They are the building blocks")]),
    Copy("B", 28, "import keyword"),
    Copy("B", 29, "Running ahaed of myself: `=` is the `assignment` operator in Python. Once used, the variable contains the assigned value.",
         edits=[R("ahaed", "ahead")]),
    Copy("B", 30, "# = to assign"),
    Copy("B", 31, "# Store a number in the variable \"number\""),
    Copy("B", 32, "**Try it yourself**: Calculate the sum of `number` and `number`, store it in a variable `number_plus`, and print out the value of `number_plus`"),
    Copy("B", 33, "# Store the value of \"number\" + \"number\" in \"number_plus\" and print the value"),
    Copy("B", 36, "# Data Types",
         edits=[H("# Data Types", "### Data types"),
                H("- **Date/Time** (`datetime.date`, `datetime.datetime`)", None)]),
    Copy("B", 38, "## Numeric",
         edits=[H("## Numeric", "#### Numbers"),
                R("[Python documentation for numbers.](https://python.swaroopch.com/op_exp.html)",
                  "[Python documentation for numbers.](https://docs.python.org/3/tutorial/introduction.html#numbers)")]),
    Copy("B", 39, "# Integer"),
    Copy("B", 40, "## Text (Strings)",
         edits=[H("## Text (Strings)", "#### Text (strings)")]),
    Copy("B", 41, "# Store the string \"Hello, I'm Spot the cat. It's nice to meet you.\""),
    Copy("B", 42, "**Indexing**", same="learner", fexpect="### Indexing"),
    Copy("B", 43, "# Find a character in a string by index"),
    Copy("B", 44, "# Slice to get the first 3 characters"),
    Copy("B", 56, "## Logical / Boolean",
         edits=[H("## Logical / Boolean", "#### True and False (booleans)")]),
    Copy("B", 57, "dog_is_cute = True", text="dog_is_cute = True\ndog_is_cute"),

    md("sec-4", "## 4. Lists and dictionaries"),
    Copy("B", 61, "# Data Structures",
         edits=[H("# Data Structures", None),
                R("We'll explore three widely used structures:", "We'll explore two widely used structures:")]),
    Copy("B", 62, "## Lists - 1-D sequences",
         edits=[H("## Lists - 1-D sequences", "### Lists")]),
    Copy("B", 63, "# An example of a list of strings (cat_toys)"),
    Copy("B", 64, "# Python allows you to create lists containing elements of different types",
         ltext="# Python allows you to create lists containing elements of different types",
         ftext="# Python allows you to create lists containing elements of different types\n"
               "mixed = [\"alp\", 34, True]\nmixed"),
    Copy("B", 65, "Indexing is not exclusive to strings. We can slice lists too!"),
    Copy("B", 66, "# Get a list item by index"),
    code("slice", "# Slice the first two items (the end index is left out)", fadd="cat_toys[0:2]"),
    Copy("B", 67, "# Replace an element \"in place\" via its index"),
    Copy("B", 68, "**Try it yourself**: Create a list containing mixed-type data. Add your:"),
    Copy("B", 69, "my_info = []", fexpect="my_info = [\"Alp\", \"Tezbasaran\", 34, True]"),
    Copy("B", 70, "#### Dictionaries",
         edits=[H("#### Dictionaries", "### Dictionaries")]),
    Copy("B", 71, "# Define a dictionary of cat names and their breed"),
    Copy("B", 72, "# You can access the value of a dictionary by calling its key pair"),
    Copy("B", 73, "# You can add new keys and values to a dictionary"),
    Copy("B", 74, "**Try it Yourself:** Print out \"Spot's\" birthday from the `birthdays` dictionary.",
         same="learner", fexpect="**Try it Yourself:** Print out \"Spot's\" birthday from the `birthdays` dictionary."),
    Copy("B", 75, "birthdays = {"),
    code("birthday", "# Print Spot's birthday", fadd="birthdays[\"Spot\"]"),

    md("sec-5", "## 5. Arithmetic"),
    md("arith-intro",
       "Python does arithmetic with `+` `-` `*` `/` `//` (floor division) `**` (power) `%` (remainder). "
       "Watch the data type of each result."),
    Copy("B", 79, "# Addition"),
    Copy("B", 80, "# Division (note the data type of the output)"),
    Copy("B", 81, "# Floor Division, rounding down to nearest integer (\"floor\")"),
    Copy("B", 82, "# Multiplication (note the data type of the output)"),
    Copy("B", 83, "**Try it Yourself**: What is 400 times 4, divided by 14, plus 39?"),
    Copy("B", 84, "# Enter the mathematical equation"),

    md("break", "## Break\n\nFive minutes. Part 2 continues below, in this same notebook, "
                "so everything you've made is still here."),

    # ---- Part 2 ---------------------------------------------------------
    md("part-2", "# Part 2: Control flow and functions"),

    md("sec-6", "## 6. Comparison and logical operators"),
    Copy("L", 1, "## 2.&nbsp;Control flow",
         edits=[H("## 2.&nbsp;Control flow", None)]),
    Copy("L", 2, "### 2.1&nbsp;Comparison Operators",
         edits=[H("### 2.1&nbsp;Comparison Operators", "### Comparison operators")]),
    Copy("L", 3, "# Compare numbers"),
    Copy("L", 4, "# Compare strings"),
    Copy("L", 5, "# Compare other expressions using multiple data types"),
    Copy("L", 6, "**Try it yourself:** What is the result of this comparison?"),
    Copy("L", 7, "# First guess then execute the cell", same="learner", fexpect="len([1, 22, 5]) == 2"),
    Copy("L", 8, "# First guess then execute the cell", same="learner", fexpect="len('alp') > len('tezbasaran')"),
    Copy("L", 9, "### 2.2&nbsp;Logical Operators",
         edits=[H("### 2.2&nbsp;Logical Operators", "### Logical operators")]),
    Copy("L", 10, "# Define a variable to use in the following examples"),
    Copy("L", 11, "# The \"and\" operator checks if both conditions are True"),
    Copy("L", 12, "# The \"or\" operator checks if at least one of the conditions are True"),
    Copy("L", 13, "# The \"not\" operator returns the opposite of the return of a comparison"),
    Copy("L", 15, "**Try it Yourself:** Write a statement that checks if a number is less than 10 and greater than zero."),
    Copy("L", 16, "# Write your code here", fexpect="num < 10 and num > 0"),

    md("sec-7", "## 7. if, elif and else"),
    Copy("L", 19, "## 3&nbsp;Branching",
         edits=[H("## 3&nbsp;Branching", None),
                H("### 3.1&nbsp;If Statements", "### if statements")]),
    Copy("L", 20, "# Write a simple if statement", fexpect="if False:"),
    Copy("L", 21, "#### 3.2&nbsp;If, Else (`if`, `else`)",
         edits=[H("#### 3.2&nbsp;If, Else (`if`, `else`)", "### if and else")]),
    Copy("L", 22, "# If statements (conditional execution)"),
    Copy("L", 23, "#### 3.3&nbsp;If, Else if, Else (`if`, `elif`, `else`)",
         edits=[H("#### 3.3&nbsp;If, Else if, Else (`if`, `elif`, `else`)", "### if, elif and else")]),
    Copy("L", 24, "# You can use if, else if (\"elif\"), and else to specify more than one condition"),
    Copy("L", 27, "Additionally, you can use the logical comparisons `in` and `not in` to evaluate if a value is or is not in a list."),
    Copy("L", 28, "# A list of my cats"),

    md("sec-8", "## 8. for loops"),
    Copy("L", 31, "## 4&nbsp;Repeats",
         edits=[H("## 4&nbsp;Repeats", None), H("### 4.1&nbsp;For loops", None)]),
    Copy("L", 32, "# Iterate over a range using the \"range()\" function",
         fedits=[R("for alp in range(10, 100, 10):",
                   "for i in range(5):\n    print(i)\n\nfor alp in range(10, 100, 10):")]),
    Copy("L", 33, "# Iterate over a string"),
    Copy("L", 34, "# For loops let you iterate over a list", same="learner",
         fadd="for name in cat_names:\n    print(name, len(name))"),
    Copy("L", 40, "**Try it yourself**: Use a for loop to iterate through the list `fruits = [\"apple\", \"banana\", \"orange\", \"grape\"]` and print each fruit with a message like \"I like [fruit]\"."),
    Copy("L", 41, "# Iterate through a list of fruits using a for loop"),
    Copy("L", 36, "# You can combine types of control flow, this is called \"nesting\"",
         ltext="# You can combine types of control flow, this is called \"nesting\"\n"
               "# Print only the names with 5 or more letters",
         ftext="# You can combine types of control flow, this is called \"nesting\"\n"
               "# Print only the names with 5 or more letters\n"
               "for name in cat_names:\n  if len(name) >= 5:\n    print(name)"),

    md("sec-9", "## 9. Methods and dot notation"),
    Copy("L", 44, "## 5&nbsp;Functions",
         edits=[H("## 5&nbsp;Functions", None)]),
    Copy("L", 45, "### 5.1&nbsp;Built-in functions",
         edits=[H("### 5.1&nbsp;Built-in functions", "### Built-in functions")]),
    Copy("L", 50, "### 5.2&nbsp;Method functions",
         edits=[H("### 5.2&nbsp;Method functions", "### Methods")]),
    Copy("L", 51, "### 5.2.1&nbsp;String Methods",
         edits=[H("### 5.2.1&nbsp;String Methods", "#### String methods")]),
    Copy("L", 52, "word = \"python\""),
    Copy("L", 62, "### 5.2.2&nbsp;List Methods",
         edits=[H("### 5.2.2&nbsp;List Methods", "#### List methods")]),
    code("rebuild",
         "# cat_toys from Part 1, rebuilt so this section runs on its own\n"
         "cat_toys = [\"feather\", \"string\", \"laser\"]\ncat_toys"),
    code("append",
         "# Add \"catnip\" with append. append changes the list itself: run this cell twice.",
         fadd="cat_toys.append(\"catnip\")\ncat_toys"),

    md("sec-10", "## 10. Your own functions"),
    Copy("L", 76, "### 5.3&nbsp;User Defined Functions",
         edits=[H("### 5.3&nbsp;User Defined Functions", None)]),
    Copy("L", 77, "#### 5.3.1&nbsp; Defining a function",
         edits=[H("#### 5.3.1&nbsp; Defining a function", "### Defining a function")]),
    Copy("L", 78, "# Define a function named \"print_hello\" that prints out a hello message -- note"),
    Copy("L", 79, "#### 5.3.2&nbsp;Returning data from a function",
         edits=[H("#### 5.3.2&nbsp;Returning data from a function", "### Returning data from a function")]),
    Copy("L", 80, "# Define a function named \"return_hello\" that returns a hello message"),
    Copy("L", 81, "Return values can be stored in variables and used just like other values"),
    Copy("L", 82, "# Store the return value of \"return_hello\""),
    Copy("L", 83, "#### 5.3.3&nbsp;Function parameters",
         edits=[H("#### 5.3.3&nbsp;Function parameters", "### Function parameters")]),
    Copy("L", 84, "# Define a function named \"return_hello_personal\" that returns a personalized"),
    Copy("L", 85, "Arguments passed to a function can be variables"),
    Copy("L", 86, "# Define variables to pass into personalized hello message function",
         edits=[R("session = \"Getting Started with Python - Loops and Functions\"",
                  "session = \"Accelerated Intro to Python\"")]),
    Copy("L", 89, "**Try it yourself:** Create a function named `add_nums` that takes two numbers as arguments and returns the results of adding these two numbers"),
    Copy("L", 90, "# Define a function that returns the results of adding two numbers passed as"),

    # ---- After the session ---------------------------------------------
    md("after", "# After the session"),

    md("sec-extra", "## If we have time"),
    md("extra-intro", "Extra examples for the session if time allows. They're good practice too."),
    Copy("L", 25, "# You can also add logical operators (and, or, not) to evaluate expressions.",
         fedits=[R("persisten stranger", "persistent stranger")]),
    Copy("L", 26, "# Comparing numbers in an if statement"),
    Copy("L", 35, "# There are a few ways to iterate over a dictionary, depending on the part of"),
    Copy("L", 87, "#### 5.3.4&nbsp;Using functions",
         edits=[H("#### 5.3.4&nbsp;Using functions", "### Using functions")]),
    Copy("L", 88, "# Define a function that replaces periods with exclamation marks in a string"),

    md("sec-practice", "## Practice at home"),
    md("practice-intro",
       "Each cell stands on its own, so it runs in a fresh session. Answers are in the filled notebook."),
    Copy("B", 34, "---",
         edits=[H("---", None),
                H("### Question: Will it be a valid **variable name** in Python?", "### Valid variable names")]),
    Copy("B", 35, "# Try the variable names"),
    Copy("B", 47, "**Try it yourself**: Use indexing and assignment to set a variable to the last word (is) in the following example.",
         pre="### The last word\n\n"),
    Copy("B", 48, "# Start with this string"),
    Copy("B", 76, "**Bonus Try it Yourself:** Add \"Sparky\" to the `birthdays` dictionary with the birthday \"May 10\"",
         same="learner", pre="### Add Sparky\n\n",
         fexpect="**Bonus Try it Yourself:** Add \"Sparky\" to the `birthdays` dictionary with the birthday \"May 10\""),
    code("sparky",
         "birthdays = {\n    \"Bill\": \"Sept 5\",\n    \"Spot\": \"April 19\",\n    \"Apple\": \"June 30\",\n"
         "    \"Carla\": \"Dec 21\"\n}\n\n# Add Sparky",
         fadd="birthdays[\"Sparky\"] = \"May 10\"\nbirthdays"),
    Copy("B", 85, "**Bonus Try it Yourself:** What is the datatype of the output from the previous cell?",
         text="### Data type of a result\n\nWhat is the data type of `(400 * 4) / 14 + 39`? Use `type()`."),
    Copy("B", 86, "", fexpect="# Datatype of the previous expression",
         ltext="# Data type of (400 * 4) / 14 + 39",
         ftext="# Data type of (400 * 4) / 14 + 39\nresult = (400 * 4) / 14 + 39\ntype(result)"),
    Copy("L", 29, "**Try it yourself:** Write an if statement that prints out a message based on membership in the *International Cats of Mystery* service. Two lists are provided below, one for current members and one for new members.",
         pre="### International Cats of Mystery\n\n"),
    Copy("L", 30, "# Current members",
         fedits=[R("Already a member", "Thank you for being a member!"),
                 R("You need cuddle to become member!",
                   "Would you like to join the International Cats of Mystery?")]),
    Copy("L", 91, "**Bonus Try it yourself:** Create a function named `count_a` that takes a list of single letters and returns the count of the occurrence of the letter \"a\"",
         pre="### count_a\n\n"),
    Copy("L", 92, "# A function that returns the count of \"a\"s in a list of letters"),
    Copy("B", 101, "## Bonus Section: Errors and troubleshooting",
         edits=[H("## Bonus Section: Errors and troubleshooting", "### Errors and troubleshooting")]),
    Copy("B", 102, "# Referencing an undefined variable results in a \"NameError\"", tags=RAISES),
    Copy("B", 103, "# Using incorrect Python syntax results in a \"SyntaxError\"", tags=RAISES),
    Copy("B", 104, "# Referencing an index that is out of range results in an \"IndexError\"", tags=RAISES),
    Copy("B", 105, "# Referencing a dictionary key that is not valid results in a \"KeyError\"", tags=RAISES),
    Copy("B", 106, "# Applying a function or operation to an incorrect data type results in a", tags=RAISES),
    Copy("B", 107, "**Try it yourself**: Run each cell below to identify the error and then edit the code to fix each error"),
    Copy("B", 108, "'This is a good string.'", tags=RAISES, ftags=None,
         ftext="'This is a good string.'\n\"Isn't this string okay?\"\n"
               "\"Pretty sure this is a good string.\"\n\"Is there something wrong with this string?\""),
    Copy("B", 109, "bank_accounts = {", tags=RAISES, ftags=None,
         fedits=[R("bank_accounts['saving']", "bank_accounts['savings']")]),
    Copy("B", 110, "count = [1, 2, 3, 4, 5]", tags=RAISES, ftags=None,
         fedits=[R("count[5]", "count[4]")]),
    Copy("B", 111, "1 + 2 + \"3\"", tags=RAISES, ftags=None, ftext="1 + 2 + 3"),
    md("grade-analyzer",
       "### Student Grade Analyzer\n\n"
       "A longer challenge that combines `if`, loops and functions: see *6 Final Activity* in the "
       f"[full Loops and Functions notebook]({URL_LOOPS}). "
       f"The [filled version]({URL_LOOPS_F}) has a worked solution."),

    md("sec-keep-going", KEEP_GOING),
]

# Cells whose learner lines are intentionally not a subset of the filled cell:
# B108-B111 are the broken cells the learner fixes (plan); B69 keeps the source's
# `my_info = []` scaffold in the learner (see report).
EXEMPT_SUBSET = {"B108", "B109", "B110", "B111", "B69"}


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def to_lines(text):
    text = text.strip("\n")
    return text.splitlines(keepends=True)


def make_cell(cid, cell_type, text, tags):
    meta = {"tags": list(tags)} if tags else {}
    if cell_type == "markdown":
        return {"cell_type": "markdown", "id": cid, "metadata": meta, "source": to_lines(text)}
    return {"cell_type": "code", "execution_count": None, "id": cid, "metadata": meta,
            "outputs": [], "source": to_lines(text)}


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": [], "toc_visible": True},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build(src_cells):
    learner, filled, labels = [], [], []
    for entry in MANIFEST:
        cid = entry.cell_id(src_cells)
        lt, ltext, ltags = entry.build(src_cells, filled=False)
        ft, ftext, ftags = entry.build(src_cells, filled=True)
        assert lt == ft, f"{entry.label}: cell types differ between versions"
        learner.append(make_cell(cid, lt, ltext, ltags))
        filled.append(make_cell(cid, ft, ftext, ftags))
        labels.append(entry.label)
    return learner, filled, labels


def src_text(cell):
    return "".join(cell["source"])


def check(learner, filled, labels):
    # 1. same count, ids, types
    assert len(learner) == len(filled), "cell counts differ"
    for a, b in zip(learner, filled):
        assert a["id"] == b["id"], f"ids differ: {a['id']} / {b['id']}"
        assert a["cell_type"] == b["cell_type"], f"types differ at {a['id']}"
    # 4. ids unique and well formed
    ids = [c["id"] for c in learner]
    assert len(set(ids)) == len(ids), "duplicate ids: " + str(sorted({i for i in ids if ids.count(i) > 1}))
    for i in ids:
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", i), f"bad id {i!r}"
    for n, (a, b, label) in enumerate(zip(learner, filled, labels)):
        if a["cell_type"] == "markdown":
            # 2. markdown identical except the title and B34
            if label not in ("new-title", "B34"):
                assert src_text(a) == src_text(b), f"markdown differs at {label}"
        else:
            # 3. every non-comment, non-blank learner line appears in the filled cell
            if label in EXEMPT_SUBSET:
                continue
            f_lines = {l.rstrip() for l in src_text(b).splitlines()}
            for line in src_text(a).splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                assert line.rstrip() in f_lines, f"{label}: learner line missing from filled cell: {line!r}"
    # extra guards of my own
    for nb in (learner, filled):
        for c in nb:
            t = src_text(c)
            assert "&nbsp;" not in t, f"residual &nbsp; in {c['id']}"
            assert c["metadata"] in ({}, {"tags": ["raises-exception"]}), c["id"]
            if c["cell_type"] == "code":
                assert c["outputs"] == [] and c["execution_count"] is None


def outline(cells):
    lines, in_fence = [], False
    for c in cells:
        if c["cell_type"] != "markdown":
            continue
        for line in src_text(c).splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m and not in_fence:
                lines.append("  " * (len(m.group(1)) - 1) + m.group(2))
    return lines


def check_urls():
    yml = ROOT / "site" / "_variables.yml"
    if not yml.exists():
        return
    body = yml.read_text(encoding="utf-8")
    for u in (URL_LEARNER, URL_FILLED, URL_BASICS, URL_BASICS_F, URL_LOOPS, URL_LOOPS_F, URL_EDA, URL_EVAL, URL_HELP):
        assert u in body, f"URL not in site/_variables.yml: {u}"


def dump(nb):
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=DEFAULT_SRC, help="getting-started-with-python checkout")
    args = ap.parse_args()
    src = Path(args.src).expanduser()

    src_cells = load_source(src)
    check_urls()
    learner, filled, labels = build(src_cells)
    check(learner, filled, labels)

    OUT_LEARNER.parent.mkdir(parents=True, exist_ok=True)
    OUT_LEARNER.write_text(dump(notebook(learner)), encoding="utf-8")
    OUT_FILLED.write_text(dump(notebook(filled)), encoding="utf-8")

    print(f"Source commit {COMMIT}; assertions passed.")
    print(f"Wrote {OUT_LEARNER.relative_to(ROOT)} ({len(learner)} cells)")
    print(f"Wrote {OUT_FILLED.relative_to(ROOT)} ({len(filled)} cells)")
    print("\nTable of contents:")
    for line in outline(learner):
        print(line)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        sys.exit(f"build failed: {e}")
