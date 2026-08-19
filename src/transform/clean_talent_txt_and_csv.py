import pandas as pd 
from fuzzywuzzy import fuzz
import re

df = pd.read_csv('raw_applications_data.csv')

print(df.duplicated().sum())


def standardise_names(df, column, threshold=80):
    

    names = df[column].dropna().unique()
    

    simialr_pairs = []

    for i in range(len(names)):
        for j in range (i + 1, len(names)):
            name1 = names[i]
            name2 = names[j]


            if name1 == name2:
                continue

            match_score = fuzz.ratio(name1, name2)

            if match_score >= threshold:
                simialr_pairs.append({"name1": name1, "name2": name2, "score": match_score})

    return pd.DataFrame(simialr_pairs)

def fix_names(df):
    names = df["invited_by"].dropna().unique()

    for i in range(len(names)):
        for j in range (i + 1, len(names)):
            name1 = names[i]
            name2 = names[j]


            if name1 == name2:
                continue

            match_score = fuzz.ratio(name1, name2)

            if match_score >= 85:
                df["invited_by"] = df["invited_by"].replace(name2, name1)
    return df

GRADE_MAP = {
    "1st": "1:1",
    "3rd": "3:1",
}

def standardise_grades(df):
    df = df.copy()
    df["degree"] = df["degree"].replace(GRADE_MAP)
    return df


def get_month_and_year(df):
    df['month'] = df['source_file'].str.extract(
        r'^(jan|feb|march|april|may|june|july|aug|sep|oct|nov|dec)',
        flags=re.IGNORECASE
    )
    df['year'] = df['source_file'].str.extract(r'(\d{4})')


    return df
    

if __name__ == "__main__":

    date_fix = get_month_and_year(df)
    print(date_fix)

    inv_similar_names = standardise_names(df, "invited_by")
    print("Fuzzy matches before fix:")
    print(inv_similar_names)

    df = fix_names(df)  # reassign — fix_names mutates in place but reassigning is safest

    remaining = standardise_names(df, "invited_by")
    print("Fuzzy matches after fix (should be empty):")
    print(remaining)

    df.to_csv('clean_talent_applications_data.csv', index=False)




