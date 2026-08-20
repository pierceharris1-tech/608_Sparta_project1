
import pandas as pd
import ast


'''
DONE:
1. name standardisation 
2. remove duplicates


'''

# Made the names Joe Bloggs format 
def standardize_names(df):
    # Clean up candidate names by removing extra spaces
    # and making capitalization consistent
    df = df.copy()

    df["name"] = df["name"].str.strip().str.title()

    return df

#Get rid of duplicate rows 

def find_duplicates(df):
    columns_to_check = [col for col in df.columns if col != "talent_id"]
    duplicates = df[df.duplicated(subset='name', keep=False)].copy()
    return duplicates

#print(find_duplicates(df))

#print(len(find_duplicates(df)))

def find_true_duplicate_names(df):
    """Return a list of names where every column matches except talent_id -
    i.e. names we're confident are true duplicates, not just people who
    happen to share a name."""

    grouped = df.groupby("name")
    duplicate_names = []

    for name, group in grouped:
        if len(group) < 2:
            continue

        rows = group.to_dict("records")
        first_row = rows[0]

        for other_row in rows[1:]:
            differences = []

            for column in df.columns:
                if column == "talent_id":
                    continue

                if first_row[column] != other_row[column]:
                    differences.append(column)

            if not differences:
                duplicate_names.append(name)

    return duplicate_names

def remove_duplicates(df):
    true_dupes = find_true_duplicate_names(df)
    rows_to_drop = df[df["name"].isin(true_dupes) & df.duplicated(subset="name", keep="first")].index

    df = df.drop(rows_to_drop)

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
        lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, dict) else {})
    )

    tech_scores_df = pd.json_normalize(tech_scores).add_prefix("Self_score_")

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
        df = remove_duplicates(df)
        return df


if __name__ == "__main__":
    #from src.extract.s3_reader import load_all_talent_data

    #talent_df = load_all_talent_data()
    csv = 'raw_talent_data.csv'
    df = pd.read_csv(csv)
    talent_df = df

    print("Before transformation:")
    print(talent_df.shape)
    print(talent_df.head())

    talent_df = clean_talent_data(talent_df)

    print("\nAfter transformation:")
    print(talent_df.shape)
    print(talent_df.head())
    print("\nColumns:")
    print(talent_df.columns.tolist())

    talent_df.to_csv('clean_talent_data.csv', index=False)

