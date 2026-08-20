from doctest import DocFileCase
import pandas as pd 
df = pd.read_csv('raw_academy_data.csv')

df_after = pd.read_csv('cleaned_academy_data.csv')


def validate_missing_values(df):
    print("\n--- Missing Values ---")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("No missing values found.")
    else:
        print(missing[missing > 0])


def validate_duplicates(df):
    print("\n--- Duplicate Rows ---")
    duplicates = df.duplicated().sum()
    print(f"Duplicate rows: {duplicates}")


def validate_required_columns(df):
    print("\n--- Required Columns ---")
    required_columns = ["name", "trainer"]
    for column in required_columns:
        if column in df.columns:
            print(f"{column}: OK")
        else:
            print(f"{column}: MISSING")


def validate_scores(df):
    print("\n--- Score Validation ---")
    score_columns = [
        column for column in df.columns
        if "_W" in column
    ]
    all_scores = df[score_columns].stack()
    invalid_scores = all_scores[
        (all_scores < 0) | (all_scores > 8)
    ]
    print(f"Total score values checked: {len(all_scores)}")
    print(f"Invalid scores: {len(invalid_scores)}")
    if len(invalid_scores) > 0:
        print("Invalid score values:")
        print(invalid_scores.head(10).tolist())

if __name__ == "__main__":
    # Load Academy data
    academy_df = df
    print("Before cleaning:")
    print(academy_df.shape)
    # Clean Academy data
    academy_df = df_after
    print("\nAfter cleaning:")
    print(academy_df.shape)
    # Run validation checks
    validate_missing_values(academy_df)
    validate_duplicates(academy_df)
    validate_required_columns(academy_df)
    validate_scores(academy_df)
