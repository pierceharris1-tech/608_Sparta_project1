from doctest import DocFileCase
import pandas as pd 
df_after = pd.read_csv('clean_talent_data.csv')

df = pd.read_csv('raw_talent_data.csv')


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
    required_columns = ["name", "talent_id"]
    for column in required_columns:
        if column in df.columns:
            print(f"{column}: OK")
        else:
            print(f"{column}: MISSING")




if __name__ == "__main__":
    # Load Academy data
    academy_df_before_clean = df
    print("Before cleaning:")
    print(academy_df_before_clean.shape)
    # Clean Academy data
    academy_df = df_after
    print("\nAfter cleaning:")
    print(academy_df.shape)
    # Run validation checks
    validate_missing_values(academy_df)
    validate_duplicates(academy_df)
    validate_required_columns(academy_df)

