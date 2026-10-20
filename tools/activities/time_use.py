"""Activity: How People Spend Their Day (American Time Use Survey).

The cells for tools/build_activities.py. Edit them here, then run
`python3 tools/build_activities.py`; hand edits to the notebooks are overwritten.

Reading the cells: md() is a markdown cell, the same in both notebooks. code(slug, learner, filled=...)
is a code cell: `learner` is the comment scaffold, `filled` is the answer (or `fadd=` lines
appended to the learner text). A cell with no `filled` and no `fadd` is "given": the same code in
both. The builder checks that every learner code line appears in the filled cell.
"""

import textwrap

from build_notebooks import COLAB, URL_EDA, URL_HELP, URL_SITE, code, md

SLUG = "time-use"
ID_PREFIX = "tu"

URL_LEARNER = f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{SLUG}.ipynb"
URL_FILLED = f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{SLUG}-solutions.ipynb"
URL_PAGE = f"{URL_SITE}activities/{SLUG}.html"
URL_POLARS = "https://docs.pola.rs/"
URL_ATUS = "https://www.bls.gov/tus/"


def T(text):
    """Dedent a triple-quoted block so the cells below can be indented."""
    return textwrap.dedent(text).strip("\n")


# ----------------------------------------------------------------------------
# Title (the only markdown that differs between the two notebooks)
# ----------------------------------------------------------------------------

TITLE_BODY = T('''
    Data Science Training Intensive · NC State University Libraries, Data Science Services

    **The data:** 2,000 people's diaries from the American Time Use Survey (ATUS), 2003–2023. It's the same file the DSTI spreadsheets track cleans in Google Sheets, so you can compare answers.

    **The question:** How do people split their day between household chores and leisure, by number of children and by work status?

    Part 1 uses the plain Python from the intro session. Part 2 does the same and more with Polars, the library from the next workshop.

    This takes about 45 minutes. Run the cells from the top, one at a time.
''')

TITLE_TAIL = T(f'''
    **Using Colab?** Click **Copy to Drive** first.

    Activity page: [{URL_PAGE}]({URL_PAGE})
''')

TITLE_LEARNER = (
    "# Activity: How People Spend Their Day\n\n" + TITLE_BODY + "\n\n"
    f"This is the learner notebook: write the code under each comment. The [filled notebook]({URL_FILLED}) has every answer.\n\n"
    + TITLE_TAIL
)

TITLE_FILLED = (
    "# Activity: How People Spend Their Day: Filled\n\n" + TITLE_BODY + "\n\n"
    f"This is the filled notebook: every exercise has an answer, so check your work here. To do the activity yourself, use the [learner notebook]({URL_LEARNER}).\n\n"
    + TITLE_TAIL
)


# ----------------------------------------------------------------------------
# The other cells, in order
# ----------------------------------------------------------------------------

CELLS = [
    # ---- Get the data ---------------------------------------------------
    md("sec-data", T('''
        ## Get the data

        Two files hold the data. `atus_working.csv` is the one you clean. It has mistakes in it on purpose. `atus_raw.csv` has the original survey codes. It's the source of truth.

        Source: American Time Use Survey (U.S. Bureau of Labor Statistics), via ICPSR study 36268. The DSTI team sampled 2,000 respondents from diary years 2003–2023.
    ''')),
    code("get-data", T('''
        # Download the two data files into this folder (skipped if they're already here)
        from pathlib import Path
        from urllib.request import urlretrieve

        BASE = "https://ncsu-libraries.github.io/dsti-python/data/"
        for name in ["atus_working.csv", "atus_raw.csv"]:
            if not Path(name).exists():
                urlretrieve(BASE + name, name)
                print("Downloaded", name)
    ''')),

    # ---- Part 1 ---------------------------------------------------------
    md("part-1", "# Part 1: Plain Python"),

    md("sec-1", T('''
        ## 1. Read the file

        The `csv` module reads a CSV file into a list of dictionaries. There is one dictionary per row, with the column names as keys.

        `with` opens the file and closes it again when the indented block ends. (`newline=""` and `encoding="utf-8"` are settings the `csv` module likes.)
    ''')),
    code("read-csv", T('''
        import csv

        with open("atus_working.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    ''')),
    code("row-count", "# How many rows are there?", fadd="len(rows)"),
    code("first-row", "# Look at the first row", fadd="rows[0]"),
    md("text-note", "Every value is text, even Age (`'78'`). The `csv` module doesn't guess types."),

    md("sec-2", T('''
        ## 2. Count the values in a column

        A dictionary can count things. The keys are the values you've seen, and each value is how many times you've seen it.
    ''')),
    code("count-values",
         T('''
            # Write count_values(column): return a dictionary of how often each value appears
            # Hint: start with counts = {}, loop over rows, and use if/else

            # Then count the Sex column
         '''),
         filled=T('''
            # Write count_values(column): return a dictionary of how often each value appears
            # Hint: start with counts = {}, loop over rows, and use if/else
            def count_values(column):
                counts = {}
                for row in rows:
                    value = row[column]
                    if value in counts:
                        counts[value] = counts[value] + 1
                    else:
                        counts[value] = 1
                return counts

            # Then count the Sex column
            count_values("Sex")
         ''')),
    md("sex-note", "Four of these values shouldn't be there. Can you spot them?"),
    code("count-edu", "# Your turn: count the Education level column", fadd='count_values("Education level")'),
    md("edu-note",
       "Some values have stray spaces at the start or the end. Some are missing an apostrophe: `Bachelors` "
       "instead of `Bachelor's`. Part 2 fixes them."),

    md("sec-3", T('''
        ## 3. A function that cleans a value

        Three fixes tidy the Sex column.

        - `.strip()` removes spaces at the ends.
        - `.title()` fixes the capitals, so `"MALE"` becomes `"Male"`.
        - A dictionary of known typos fixes the rest.
    ''')),
    code("clean-sex",
         T('''
            fixes = {"Femal": "Female", "Mole": "Male"}

            # Write clean_sex(value): strip, fix capitals with .title(), then replace known typos using fixes
         '''),
         filled=T('''
            fixes = {"Femal": "Female", "Mole": "Male"}

            # Write clean_sex(value): strip, fix capitals with .title(), then replace known typos using fixes
            def clean_sex(value):
                value = value.strip().title()
                if value in fixes:
                    return fixes[value]
                return value
         ''')),
    code("test-clean", "# Test it on each messy value",
         fadd=T('''
            for value in ["Femal", "female", "MALE", "Mole"]:
                print(value, "->", clean_sex(value))
         ''')),
    code("apply-clean", "# Clean every row, then count Sex again",
         fadd=T('''
            for row in rows:
                row["Sex"] = clean_sex(row["Sex"])

            count_values("Sex")
         ''')),

    md("sec-4", T('''
        ## 4. Find an impossible age

        ATUS ages run 15–85. The values 80 and 85 are top codes: they stand for older groups of people.

        Ages are text too. `int()` turns text into a whole number, so `int('78')` gives the number `78`. You need it to compare an age with 85.
    ''')),
    code("old-age", "# Print the Case and Age of anyone older than 85",
         fadd=T('''
            for row in rows:
                if int(row["Age"]) > 85:
                    print(row["Case"], row["Age"])
         ''')),
    md("age-note", T('''
        Someone is 150. You can't tell the real age from this file, so don't guess. Part 2 marks it as missing, and it checks the source file for another age problem.

        That was a lot of looping for one column. Polars works on a whole column at once.
    ''')),

    # ---- Part 2 ---------------------------------------------------------
    md("part-2", "# Part 2: Polars"),

    md("sec-5", T('''
        ## 5. Load the data with Polars

        Polars is a library for tables of data. If you haven't installed it yet:

        - **In `dss-python`:** run `uv add polars` in a terminal. JupyterLab has one: **File → New → Terminal**. Then choose **Kernel → Restart Kernel**. Run the Get the data cell again only if the files are missing. Part 2 doesn't use anything from Part 1, so you can start again from here.
        - **With conda:** run `conda install -c conda-forge polars`.
        - **In Colab:** Polars is already there.
    ''')),
    code("import-polars", "import polars as pl"),
    md("read-note", T('''
        `pl.read_csv` reads the whole file into a DataFrame, which is a table. `null_values="NA"` tells Polars that the text `NA` means missing. Without it, the Sleep column would load as text.
    ''')),
    code("read-polars", '# Read atus_working.csv into df, with "NA" as missing, and show its shape',
         fadd=T('''
            df = pl.read_csv("atus_working.csv", null_values="NA")
            df.shape
         ''')),
    code("head", "# Look at the first rows", fadd="df.head()"),

    md("sec-6", T('''
        ## 6. Fix the text columns

        `with_columns` changes columns, and `pl.col("Sex")` picks one.

        The `.str` methods are the same ideas as `clean_sex`, applied to every row at once. `replace` takes a dictionary, like `fixes`.
    ''')),
    code("clean-text", "# Clean Sex and Education level",
         fadd=T('''
            df = df.with_columns(
                pl.col("Sex").str.strip_chars().str.to_titlecase().replace({"Femal": "Female", "Mole": "Male"}),
                pl.col("Education level").str.strip_chars().replace({"Bachelors": "Bachelor's", "Masters": "Master's"}),
            )
         ''')),
    code("check-sex", "# Check Sex with value_counts()", fadd='df["Sex"].value_counts()'),
    code("check-edu", "# Your turn: check Education level the same way", fadd='df["Education level"].value_counts()'),

    md("sec-7", T('''
        ## 7. Codes, names and missing values

        `rename` gives columns readable names. It takes a dictionary of old names and new names.

        Metropolitan still uses ATUS codes, and a dictionary turns them into labels. `None` means missing.

        In work hours, -1 (not asked) and -4 (hours vary) aren't hours, so they become missing too. So does the impossible age. `pl.when(...).then(...).otherwise(...)` is Polars' if/else for a column.

        Empty is not zero: averages skip missing values.
    ''')),
    code("rename", "# Give TRCHILDNUM and TEHRUSLT readable names",
         fadd='df = df.rename({"TRCHILDNUM": "Number of children", "TEHRUSLT": "Work hours per week"})'),
    code("metro",
         T('''
            metro = {1: "Metropolitan", 2: "Non-metropolitan", 3: "Not identified", -1: None}

            # Metropolitan codes to labels; negative work hours and ages over 85 become missing
         '''),
         filled=T('''
            metro = {1: "Metropolitan", 2: "Non-metropolitan", 3: "Not identified", -1: None}

            # Metropolitan codes to labels; negative work hours and ages over 85 become missing
            df = df.with_columns(
                pl.col("Metropolitan").replace_strict(metro),
                pl.when(pl.col("Work hours per week") < 0).then(None).otherwise(pl.col("Work hours per week")).alias("Work hours per week"),
                pl.when(pl.col("Age") > 85).then(None).otherwise(pl.col("Age")).alias("Age"),
            )
         ''')),
    code("nulls", "# How many missing values does each column have now?", fadd="df.null_count()"),

    md("sec-8", T('''
        ## 8. Duplicates

        Survey files can hold the same row twice. Check for it.
    ''')),
    code("dup-count", "# How many rows are exact copies of another row?", fadd="df.is_duplicated().sum()"),
    md("dup-note", T('''
        10 means 5 rows, each there twice. `unique()` keeps one copy of each row, and `maintain_order=True` keeps the rows in their original order.
    ''')),
    code("unique", "# Keep one copy of each row, then show the new number of rows",
         fadd=T('''
            df = df.unique(maintain_order=True)
            df.height
         ''')),
    code("case-dup", "# Does any Case ID still appear twice?", fadd='df.filter(pl.col("Case").is_duplicated())'),
    md("case-note", T('''
        The same person appears twice, with two ages: 37 and 73. Don't guess which is right. Check the source file. In `atus_raw.csv`, `TUCASEID` is the case and `TEAGE` is the age.
    ''')),
    code("raw-lookup", "# Read atus_raw.csv and look up Case 20181109182318",
         fadd=T('''
            raw = pl.read_csv("atus_raw.csv")
            raw.filter(pl.col("TUCASEID") == 20181109182318).select("TUCASEID", "TEAGE")
         ''')),
    md("drop-note", T('''
        The source says 37, so 73 is the wrong one. `filter` keeps the rows that match a condition. `~` means not and `&` means and, so the next cell keeps every row except the one with that Case and the age 73.
    ''')),
    code("drop-wrong", "# Drop the row with the wrong age, then check that every Case ID is unique",
         fadd=T('''
            df = df.filter(~((pl.col("Case") == 20181109182318) & (pl.col("Age") == 73)))
            df.height, df["Case"].n_unique()
         ''')),

    md("sec-9", T('''
        ## 9. Chores and leisure

        - **Chores** = Interior cleaning + Laundry + Food and drink prep + Kitchen clean-up.
        - **Leisure** = Reading + Playing games + TV and Movies + Socializing.

        Eating and Grocery Shopping count as neither. These are the same definitions as the spreadsheets track.
    ''')),
    code("chores-leisure",
         T('''
            chores = [
                "Interior cleaning (mins)",
                "Laundry (mins)",
                "Food and drink prep (mins)",
                "Kitchen clean-up (mins)",
            ]
            leisure = [
                "Reading (mins)",
                "Playing games (mins)",
                "TV and Movies (mins)",
                "Socializing (mins)",
            ]

            # Add Chores (mins) and Leisure (mins): the sum of each list, row by row (pl.sum_horizontal)
         '''),
         filled=T('''
            chores = [
                "Interior cleaning (mins)",
                "Laundry (mins)",
                "Food and drink prep (mins)",
                "Kitchen clean-up (mins)",
            ]
            leisure = [
                "Reading (mins)",
                "Playing games (mins)",
                "TV and Movies (mins)",
                "Socializing (mins)",
            ]

            # Add Chores (mins) and Leisure (mins): the sum of each list, row by row (pl.sum_horizontal)
            df = df.with_columns(
                pl.sum_horizontal(chores).alias("Chores (mins)"),
                pl.sum_horizontal(leisure).alias("Leisure (mins)"),
            )
         ''')),
    md("mean-note", "`select` picks columns or expressions. `.mean()` averages a column, and `.round(1)` keeps one decimal."),
    code("overall", "# Your turn: the average Chores (mins) and Leisure (mins) over everyone, to one decimal",
         fadd=T('''
            df.select(
                pl.col("Chores (mins)").mean().round(1),
                pl.col("Leisure (mins)").mean().round(1),
            )
         ''')),

    md("sec-10", T('''
        ## 10. Answer the question

        `group_by` makes one group for each value in a column, and `agg` summarizes each group. `pl.len()` counts the rows in a group, and `alias` names the new column. `clip(upper_bound=3)` puts 3 or more children in one group, so 3 means "3 or more".
    ''')),
    code("by-kids", "# Average chores and leisure by number of children (3 means 3 or more)",
         fadd=T('''
            by_kids = (
                df.with_columns(pl.col("Number of children").clip(upper_bound=3).alias("Children"))
                .group_by("Children")
                .agg(
                    pl.len().alias("People"),
                    pl.col("Chores (mins)").mean().round(1),
                    pl.col("Leisure (mins)").mean().round(1),
                )
                .sort("Children")
            )
            by_kids
         ''')),
    code("by-work", "# Your turn: the same by Labor force status, biggest group first",
         fadd=T('''
            by_work = (
                df.group_by("Labor force status")
                .agg(
                    pl.len().alias("People"),
                    pl.col("Chores (mins)").mean().round(1),
                    pl.col("Leisure (mins)").mean().round(1),
                )
                .sort("People", descending=True)
            )
            by_work
         ''')),
    md("results-note", T('''
        What you should see: more children means more chores and less leisure. People not in the labor force have the most leisure.

        These are 2,000 people, not the US. The file has no survey weights, so the numbers describe this sample only.
    ''')),

    md("sec-11", T('''
        ## 11. One chart

        You made a bar plot with matplotlib in the intro session. `plt.bar` takes the labels and the heights. `.to_list()` turns a Polars column into a list.
    ''')),
    code("chart",
         T('''
            labels = ["0", "1", "2", "3 or more"]

            # Bar chart of average chores by number of children
            # Hint: the heights are by_kids["Chores (mins)"].to_list()
         '''),
         filled=T('''
            import matplotlib.pyplot as plt

            labels = ["0", "1", "2", "3 or more"]

            # Bar chart of average chores by number of children
            # Hint: the heights are by_kids["Chores (mins)"].to_list()
            plt.bar(labels, by_kids["Chores (mins)"].to_list())
            plt.xlabel("Children in the household")
            plt.ylabel("Average chores (minutes per day)")
            plt.title("More children, more chores")
            plt.show()
         ''')),

    md("sec-12", T('''
        ## 12. Save your work

        `write_csv` saves a DataFrame as a CSV file in this folder.
    ''')),
    code("save", "# Save the clean data as atus_clean.csv", fadd='df.write_csv("atus_clean.csv")'),

    # ---- Closing --------------------------------------------------------
    md("check-numbers", T('''
        ## Check your numbers

        | What | You should see |
        |---|---|
        | Rows at the start, after `unique()`, and after dropping the wrong age | 2006, then 2001, then 2000 |
        | Sex values after cleaning | Female and Male |
        | Education level values after cleaning | 8 |
        | Missing values at the end of step 7 | Age 1, Sleep (mins) 3, Metropolitan 233, Work hours per week 839 |
        | Average chores and leisure over everyone | 74.1 and 252.2 minutes |

        Chores and leisure by number of children:

        | Children | People | Chores (mins) | Leisure (mins) |
        |---|---|---|---|
        | 0 | 1137 | 65.7 | 297.9 |
        | 1 | 323 | 66.2 | 206.9 |
        | 2 | 360 | 85.9 | 187.7 |
        | 3 or more | 180 | 117.4 | 173.5 |

        Same numbers as the spreadsheets track? Compare at the wrap-up.
    ''')),
    md("keep-going", T(f'''
        ## Keep going

        - Make the same chart for leisure.
        - Group by `Diary Day` to compare weekends and weekdays.
        - The [Exploratory Data Analysis with Polars workshop]({URL_EDA}) goes further with the same library.
        - The [Polars user guide]({URL_POLARS}) explains every method you used.
        - [The American Time Use Survey]({URL_ATUS}) has the full data and documentation.
        - Help: [go.ncsu.edu/getdatahelp]({URL_HELP})
    ''')),
]
