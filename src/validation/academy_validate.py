import pandas as pd
from src.extract.s3_reader import load_all_academy_data
from src.transform.clean_academy import clean_academy_data


if __name__ == "__main__":

    # Load Academy data
    academy_df = load_all_academy_data()

    print("Before cleaning:")
    print(academy_df.shape)
    print(academy_df.head())

    # Clean Academy data
    academy_df = clean_academy_data(academy_df)

    print("\nAfter cleaning:")
    print(academy_df.shape)
    print(academy_df.head())

    print("\nColumns:")
    print(academy_df.columns.tolist())
    print("\nMissing values:")
    missing_values = academy_df.isnull().sum()

    print(missing_values[missing_values > 0])

    print("\nInvalid scores:")

    invalid_scores = academy_df[
        (academy_df["score"] < 0) |
        (academy_df["score"] > 8)
    ]

    print("Number of invalid scores:", len(invalid_scores))

    if len(invalid_scores) > 0:
        print(invalid_scores.head())

    print("\nRequired columns validation:")

    required_columns = ["name", "trainer", "trait", "week", "score"]

    missing_columns = [
        column for column in required_columns
        if column not in academy_df.columns
    ]

    if missing_columns:
        print("Missing required columns:", missing_columns)
    else:
        print("All required columns are present.")

    print("\nDuplicate validation:")

    duplicate_count = academy_df.duplicated().sum()

    print("Number of duplicate rows:", duplicate_count)

print("\nWeek validation:")

invalid_weeks = academy_df[
    (academy_df["week"] < 1) |
    (academy_df["week"] > 10)
    ]

print("Number of invalid weeks:", len(invalid_weeks))

if len(invalid_weeks) > 0:
    print(invalid_weeks.head())

print("\nTrait validation:")

valid_traits = [
    "Analytic",
    "Independent",
    "Determined",
    "Professional",
    "Studious",
    "Imaginative"
]

invalid_traits = academy_df[
    ~academy_df["trait"].isin(valid_traits)
]

print("Number of invalid traits:", len(invalid_traits))

if len(invalid_traits) > 0:
    print(invalid_traits["trait"].unique())

print("\nName and trainer validation:")

missing_names = academy_df["name"].isnull().sum()
missing_trainers = academy_df["trainer"].isnull().sum()

print("Missing names:", missing_names)
print("Missing trainers:", missing_trainers)
print("\nScore data type validation:")

non_numeric_scores = pd.to_numeric(
    academy_df["score"],
    errors="coerce"
).isna().sum()

print("Non-numeric scores:", non_numeric_scores)

print("\nPerson-week-trait validation:")

duplicate_person_week_trait = academy_df.duplicated(
    subset=["name", "week", "trait"]
).sum()

print(
    "Duplicate person-week-trait records:",
    duplicate_person_week_trait
)