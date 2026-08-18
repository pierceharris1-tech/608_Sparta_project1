import pandas as pd


def standardize_names(df):
    # Clean up the name and trainer columns - remove extra spaces, fix capitalization
    df = df.copy()

    cleaned_names = []
    for value in df["name"]:
        cleaned_names.append(value.strip().title())
    df["name"] = cleaned_names

    cleaned_trainers = []
    for value in df["trainer"]:
        cleaned_trainers.append(value.strip().title())
    df["trainer"] = cleaned_trainers

    return df


def remove_duplicate_rows(df):
    # Remove any rows that are exact duplicates of another row
    rows_before = len(df)
    df = df.drop_duplicates()
    rows_after = len(df)

    if rows_before != rows_after:
        removed = rows_before - rows_after
        print(f"Removed {removed} duplicate row(s)")

    return df


def melt_weekly_scores(df):
    # Turn each wide row into several long rows,
    # one row per trait per available week

    traits = ["Analytic", "Independent", "Determined",
              "Professional", "Studious", "Imaginative"]

    new_rows = []

    # Find all available weeks from the column names
    weeks = set()

    for column in df.columns:
        for trait in traits:
            if column.startswith(trait + "_W"):
                week = column.replace(trait + "_W", "")
                weeks.add(int(week))

    for index, row in df.iterrows():
        name = row["name"]
        trainer = row["trainer"]

        for week in sorted(weeks):
            for trait in traits:
                column_name = trait + "_W" + str(week)

                if column_name not in df.columns:
                    continue

                score = row[column_name]

                if pd.isna(score):
                    continue

                new_rows.append({
                    "name": name,
                    "trainer": trainer,
                    "trait": trait,
                    "week": week,
                    "score": score
                })

    return pd.DataFrame(new_rows)

def validate_score_range(df):
    # Check that every score is between 0 and 8, print a warning if not
    bad_rows = []

    for index, row in df.iterrows():
        if row["score"] < 0 or row["score"] > 8:
            bad_rows.append(row)

    if len(bad_rows) > 0:
        print(f"Error: {len(bad_rows)} score(s) found outside the 0-8 range")

    return df


def clean_academy_data(df):
    # Run all the cleaning steps in order
    df = standardize_names(df)
    df = remove_duplicate_rows(df)
    df = melt_weekly_scores(df)
    df = validate_score_range(df)
    return df