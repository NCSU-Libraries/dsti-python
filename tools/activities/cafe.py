"""Activity: Campus Café Sales (synthetic data).

The cells for tools/build_activities.py. Edit them here, then run
`python3 tools/build_activities.py`; hand edits to the notebooks are overwritten.

Reading the cells: md() is a markdown cell, the same in both notebooks. code(slug, learner, filled=...)
is a code cell: `learner` is the comment scaffold, `filled` is the answer (or `fadd=` lines
appended to the learner text). A cell with no `filled` and no `fadd` is "given": the same code in
both. The builder checks that every learner code line appears in the filled cell.

Dollar signs in markdown are written `\\$` (a backslash in the notebook), because Jupyter reads a
pair of bare dollar signs as math.
"""

import textwrap

from build_notebooks import COLAB, URL_EDA, URL_HELP, URL_SITE, code, md

SLUG = "cafe"
ID_PREFIX = "cafe"

URL_LEARNER = f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{SLUG}.ipynb"
URL_FILLED = f"{COLAB}NCSU-Libraries/dsti-python/blob/main/notebooks/activity-{SLUG}-solutions.ipynb"
URL_PAGE = f"{URL_SITE}activities/{SLUG}.html"
URL_POLARS = "https://docs.pola.rs/"
URL_CLAUDE = "https://ncsu-libraries.github.io/agentic-coding-with-claude/"


def T(text):
    """Dedent a triple-quoted block so the cells below can be indented."""
    return textwrap.dedent(text).strip("\n")


# ----------------------------------------------------------------------------
# Title (the only markdown that differs between the two notebooks)
# ----------------------------------------------------------------------------

TITLE_BODY = T('''
    Data Science Training Intensive · NC State University Libraries, Data Science Services

    **The data:** a campus café's register, August 2025 to May 2026, with one row per menu item per day. The café and its sales are made up.

    **The question:** Which menu items earn the most money, and does the weather change what people buy?

    Part 1 uses the plain Python from the intro session. Part 2 does more with Polars, the library from the next workshop.

    This takes about 35 minutes. Run the cells from the top, one at a time.
''')

TITLE_TAIL = T(f'''
    **Using Colab?** Click **Copy to Drive** first.

    Activity page: [{URL_PAGE}]({URL_PAGE})
''')

TITLE_LEARNER = (
    "# Activity: Campus Café Sales\n\n" + TITLE_BODY + "\n\n"
    f"This is the learner notebook: write the code under each comment. The [filled notebook]({URL_FILLED}) has every answer.\n\n"
    + TITLE_TAIL
)

TITLE_FILLED = (
    "# Activity: Campus Café Sales: Filled\n\n" + TITLE_BODY + "\n\n"
    f"This is the filled notebook: every exercise has an answer, so check your work here. To do the activity yourself, use the [learner notebook]({URL_LEARNER}).\n\n"
    + TITLE_TAIL
)


# ----------------------------------------------------------------------------
# The other cells, in order
# ----------------------------------------------------------------------------

CELLS = [
    # ---- Get the data ---------------------------------------------------
    md("sec-data", T(f'''
        ## Get the data

        One file holds the data: `cafe_sales.csv`. Each row is one menu item on one day.

        - `date`, `item` and `category`, such as Coffee or Bakery
        - `units_sold` and `unit_price`, in dollars
        - `high_temp_f`: the campus high that day, in °F

        The café, the menu and the sales are made up. They come from the Libraries' [Agentic Coding with Claude]({URL_CLAUDE}) workshop (CC BY 4.0). The file has problems in it, on purpose.
    ''')),
    code("get-data", T('''
        # Download the data file into this folder (skipped if it's already here)
        from pathlib import Path
        from urllib.request import urlretrieve

        BASE = "https://ncsu-libraries.github.io/dsti-python/data/"
        name = "cafe_sales.csv"
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

        with open("cafe_sales.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    ''')),
    code("row-count", "# How many rows?", fadd="len(rows)"),
    code("first-row", "# Look at the first row", fadd="rows[0]"),
    md("text-note", "Every value is text, even `units_sold` (`'115'`) and `unit_price` (`'2.25'`). The `csv` module doesn't guess types."),

    md("sec-2", T('''
        ## 2. A revenue function

        Revenue is units sold times unit price. Both are text, so turn them into numbers first. `int()` turns text into a whole number, and `float()` turns text into a number with a decimal point (a float). So `int('115')` gives `115`, and `float('2.25')` gives `2.25`.
    ''')),
    code("revenue",
         T('''
            # Write revenue(row): units_sold times unit_price, as numbers
         '''),
         filled=T('''
            # Write revenue(row): units_sold times unit_price, as numbers
            def revenue(row):
                return int(row["units_sold"]) * float(row["unit_price"])
         ''')),
    code("try-revenue", "# Try it on the first row", fadd="revenue(rows[0])"),

    md("sec-3", T('''
        ## 3. Total revenue by item

        A dictionary can keep running totals. The key is the item, and the value is its total so far. It's the same pattern as counting: if the item is already a key, add this row's revenue to its total. If it isn't, start a new total.

        `round(total, 2)` keeps two decimal places, which is cents.
    ''')),
    code("totals",
         T('''
            # Build totals: each item's total revenue for the whole year
            # Hint: start with totals = {}, loop over rows, and use if/else

            # Then print each item and its total, rounded to 2 decimal places
         '''),
         filled=T('''
            # Build totals: each item's total revenue for the whole year
            # Hint: start with totals = {}, loop over rows, and use if/else
            totals = {}
            for row in rows:
                item = row["item"]
                if item in totals:
                    totals[item] = totals[item] + revenue(row)
                else:
                    totals[item] = revenue(row)

            # Then print each item and its total, rounded to 2 decimal places
            for item in totals:
                print(item, round(totals[item], 2))
         ''')),
    md("totals-note", T('''
        Two things look off. "Cold Brew" and "Cold Brew Coffee" sound like the same drink. And is Latte really that far ahead?
    ''')),

    md("sec-4", T('''
        ## 4. Find the odd price

        Look for a price that doesn't fit. `unit_price` is text, so use `float()` to compare it with a number.
    ''')),
    code("odd-price", "# Print every row whose unit_price is over $10",
         fadd=T('''
            for row in rows:
                if float(row["unit_price"]) > 10:
                    print(row)
         ''')),
    md("odd-note", T('''
        A latte for \\$45 is a typo for \\$4.50. It adds \\$3,564 of revenue that never happened. Note it: Part 2 fixes it.

        That was a lot of looping. Polars works on a whole column at once.
    ''')),

    # ---- Part 2 ---------------------------------------------------------
    md("part-2", "# Part 2: Polars"),

    md("sec-5", T('''
        ## 5. Load the data with Polars

        Polars is a library for tables of data. If you haven't installed it yet:

        - **In `dss-python`:** run `uv add polars` in a terminal. JupyterLab has one: **File → New → Terminal**. Then choose **Kernel → Restart Kernel**. Run the Get the data cell again only if the file is missing. Part 2 doesn't use anything from Part 1, so you can start again from here.
        - **With conda:** run `conda install -c conda-forge polars`.
        - **In Colab:** Polars is already there.
    ''')),
    code("import-polars", "import polars as pl"),
    md("read-note", T('''
        `pl.read_csv` reads the whole file into a DataFrame, which is a table. `try_parse_dates=True` turns the `date` text into real dates.
    ''')),
    code("read-polars", "# Read cafe_sales.csv into df, with dates parsed, and show its shape",
         fadd=T('''
            df = pl.read_csv("cafe_sales.csv", try_parse_dates=True)
            df.shape
         ''')),
    code("head", "# Look at the first rows", fadd="df.head()"),

    md("sec-6", T('''
        ## 6. Fix the two problems

        `with_columns` changes columns, and `pl.col("unit_price")` picks one.

        `pl.when(...).then(...).otherwise(...)` is an `if`/`else` for a column. `&` means and, so the first fix only touches a Latte priced at 45.0. Every other price stays as it was.

        `replace` takes a dictionary of old values and new values.
    ''')),
    code("fix",
         T('''
            # Fix the $45 latte, and call every "Cold Brew Coffee" "Cold Brew"
         '''),
         filled=T('''
            # Fix the $45 latte, and call every "Cold Brew Coffee" "Cold Brew"
            df = df.with_columns(
                pl.when((pl.col("item") == "Latte") & (pl.col("unit_price") == 45.0))
                .then(4.50)
                .otherwise(pl.col("unit_price"))
                .alias("unit_price"),
                pl.col("item").replace({"Cold Brew Coffee": "Cold Brew"}),
            )
         ''')),
    code("check-items", "# Check: count the rows for each item", fadd='df["item"].value_counts()'),
    md("fix-note", T('''
        Every item should have 264 rows now, one for each day. There are 10 items, where there were 11.

        Some prices also went up on January 7. That's a real change, not a mistake, so leave it.
    ''')),

    md("sec-7", T('''
        ## 7. Revenue by item

        Columns multiply row by row, so `pl.col("units_sold") * pl.col("unit_price")` gives the revenue of every row at once, with no loop.

        `group_by` makes one group for each item, and `agg` summarizes each group. `.round(2)` keeps cents, and `sort` with `descending=True` puts the biggest first.
    ''')),
    code("add-revenue", "# Add a revenue column: units_sold times unit_price",
         fadd='df = df.with_columns((pl.col("units_sold") * pl.col("unit_price")).alias("revenue"))'),
    code("by-item", "# Total revenue and units by item, biggest earner first",
         fadd=T('''
            by_item = (
                df.group_by("item")
                .agg(pl.col("revenue").sum().round(2), pl.col("units_sold").sum())
                .sort("revenue", descending=True)
            )
            by_item
         ''')),
    code("total", "# Total revenue for the whole year", fadd='df["revenue"].sum()'),
    md("revenue-note", T('''
        Drip Coffee sells the most cups, but Latte earns the most. It's still first, by less than it looked in Part 1. The total is \\$300,506.75.
    ''')),

    md("sec-8", T('''
        ## 8. Closed days

        On a closed day, every item sold 0. Count those days, then leave them out of the weather question. A closed day isn't a slow day.
    ''')),
    code("closed",
         T('''
            # Units sold per day, then count the days with zero
         '''),
         filled=T('''
            # Units sold per day, then count the days with zero
            daily = df.group_by("date").agg(pl.col("units_sold").sum().alias("units"))
            daily.filter(pl.col("units") == 0).height
         ''')),
    md("closed-note", "That's 33 closed days. The café was open on the other 231."),

    md("sec-9", T('''
        ## 9. Does the weather matter?

        `is_in` keeps the rows whose value is in a list. Here the list is the open days, and `.implode()` packs the dates into one list for `is_in` to use.
    ''')),
    code("open-days",
         T('''
            # Keep only open days
            # Hint: the dates in daily that have more than 0 units, then is_in
         '''),
         filled=T('''
            # Keep only open days
            # Hint: the dates in daily that have more than 0 units, then is_in
            open_days = daily.filter(pl.col("units") > 0)["date"]
            open_df = df.filter(pl.col("date").is_in(open_days.implode()))
         ''')),
    md("weather-note", T('''
        To sort days into weather groups, `pl.when(...).then(...)` can take several `.when(...)` steps. Polars checks them in order, and `.otherwise(...)` catches the rest. `pl.lit("...")` means this exact text, not a column name.
    ''')),
    code("weather",
         T('''
            # Average daily units of Iced Tea and Hot Chocolate in cold, mild and hot weather
            # Hint: below 60°F is cold, 60–79°F is mild, 80°F or warmer is hot. Group by item and weather.
         '''),
         filled=T('''
            # Average daily units of Iced Tea and Hot Chocolate in cold, mild and hot weather
            # Hint: below 60°F is cold, 60–79°F is mild, 80°F or warmer is hot. Group by item and weather.
            weather = (
                open_df.filter(pl.col("item").is_in(["Iced Tea", "Hot Chocolate"]))
                .with_columns(
                    pl.when(pl.col("high_temp_f") >= 80).then(pl.lit("80°F or warmer"))
                    .when(pl.col("high_temp_f") < 60).then(pl.lit("below 60°F"))
                    .otherwise(pl.lit("60–79°F")).alias("weather")
                )
                .group_by("item", "weather")
                .agg(pl.col("units_sold").mean().round(1), pl.len().alias("days"))
                .sort("item", "weather")
            )
            weather
         ''')),
    md("results-note", T('''
        What you should see: Hot Chocolate sells about three times as much below 60°F as at 80°F or warmer. Iced Tea goes the other way.
    ''')),

    md("sec-10", T('''
        ## 10. One chart

        To chart by month, group by `pl.col("date").dt.truncate("1mo")`, which rounds each date down to the first day of its month. `strftime("%b %Y")` writes a date as text, like `Aug 2025`, and `.to_list()` turns a Polars column into a list for `plt.bar`.
    ''')),
    code("chart",
         T('''
            # Bar chart of revenue by month
            # Hint: group by the month, sum the revenue, then plt.bar(labels, heights)
         '''),
         filled=T('''
            # Bar chart of revenue by month
            # Hint: group by the month, sum the revenue, then plt.bar(labels, heights)
            import matplotlib.pyplot as plt

            monthly = df.group_by(pl.col("date").dt.truncate("1mo").alias("month")).agg(pl.col("revenue").sum()).sort("month")
            labels = monthly["month"].dt.strftime("%b %Y").to_list()
            plt.figure(figsize=(9, 4))
            plt.bar(labels, monthly["revenue"].to_list())
            plt.ylabel("Revenue ($)")
            plt.title("Revenue by month (August and May are partial months)")
            plt.xticks(rotation=45)
            plt.show()
         ''')),
    md("chart-note", T('''
        The first and last bars are short because the data starts on August 18 and ends on May 8. December is short because the café was closed for most of the second half of the month.
    ''')),

    # ---- Closing --------------------------------------------------------
    md("check-numbers", T('''
        ## Check your numbers

        | What | You should see |
        |---|---|
        | Rows in the file | 2640 |
        | Part 1: Latte total, with the \\$45 typo | 67811.5 |
        | Part 1: Cold Brew and Cold Brew Coffee totals | 19324.75 and 16047.0 |
        | Rows for each item after the fixes | 264, for 10 items |
        | Closed days | 33 (open: 231) |
        | Total revenue | 300506.75 |

        The top 3 items by revenue:

        | Item | Revenue | Units |
        |---|---|---|
        | Latte | 64247.5 | 13868 |
        | Drip Coffee | 55638.5 | 23351 |
        | Cold Brew | 35371.75 | 8113 |

        Average units per open day, by weather:

        | Item | Weather | Units per day | Days |
        |---|---|---|---|
        | Hot Chocolate | 60–79°F | 13.4 | 110 |
        | Hot Chocolate | 80°F or warmer | 6.4 | 34 |
        | Hot Chocolate | below 60°F | 22.1 | 87 |
        | Iced Tea | 60–79°F | 21.2 | 110 |
        | Iced Tea | 80°F or warmer | 27.3 | 34 |
        | Iced Tea | below 60°F | 13.6 | 87 |
    ''')),
    md("keep-going", T(f'''
        ## Keep going

        - Try revenue by day of week with `pl.col("date").dt.weekday()`.
        - Compare fall and spring. Some prices went up on January 7: does revenue per open day change with them?
        - The [Exploratory Data Analysis with Polars workshop]({URL_EDA}) goes further with the same library.
        - The [Polars user guide]({URL_POLARS}) explains every method you used.
        - Help: [go.ncsu.edu/getdatahelp]({URL_HELP})
    ''')),
]
