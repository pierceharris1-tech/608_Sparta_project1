import pandas as pd


def standardize_names(df):
    # Clean up candidate names by removing extra spaces
    # and making capitalization consistent
    df = df.copy()

    df["name"] = df["name"].str.strip().str.title()

    return df

def remove_duplicate_rows(df):
    # Remove rows that are exact duplicates.
    # Convert list/dictionary values to strings temporarily so
    # pandas can compare them.

    rows_before = len(df)

    df = df.copy()

    duplicate_check = df.copy()

    for column in duplicate_check.columns:
        duplicate_check[column] = duplicate_check[column].apply(
            lambda x: str(x) if isinstance(x, (list, dict)) else x
        )

    duplicate_mask = ~duplicate_check.duplicated()

    df = df[duplicate_mask].copy()

    rows_after = len(df)

    if rows_before != rows_after:
        removed = rows_before - rows_after
        print(f"Removed {removed} duplicate row(s)")

    return df


def clean_date(df):
    # Convert the date column from text to a proper datetime format
    df = df.copy()

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    return df

def expand_tech_scores(df):
    # Expand the tech_self_score dictionary into separate columns
    df = df.copy()

    tech_scores = df["tech_self_score"].apply(
        lambda x: x if isinstance(x, dict) else {}
    )

    tech_scores_df = pd.json_normalize(tech_scores)

    df = pd.concat(
        [df.drop(columns=["tech_self_score"]), tech_scores_df],
        axis=1
    )

    return df

def clean_talent_data(df):
        # Run all Talent cleaning and transformation steps in order
        df = standardize_names(df)
        df = clean_date(df)
        df = expand_tech_scores(df)
        df = remove_duplicate_rows(df)

        return df


if __name__ == "__main__":
    from src.extract.s3_reader import load_all_talent_data

    talent_df = load_all_talent_data()

    print("Before transformation:")
    print(talent_df.shape)
    print(talent_df.head())

    talent_df = clean_talent_data(talent_df)

    print("\nAfter transformation:")
    print(talent_df.shape)
    print(talent_df.head())
    print("\nColumns:")
    print(talent_df.columns.tolist())


