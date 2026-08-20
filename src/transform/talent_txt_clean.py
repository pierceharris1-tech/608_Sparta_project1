
import pandas as pd 
import sys
 

def parse_sparta_day_text(raw_text):
    """Take the raw text of one Sparta Day file and turn it into a list
    of rows - one row per person per assessment type."""

    lines = raw_text.split("\n")

    # line 1 has the date, e.g. "Thursday 1 August 2019"
    date_parts = lines[0].split(" ")
    day = date_parts[1]
    month = date_parts[2]
    year = date_parts[3]
    date_text = f"{day} {month} {year}"

    # line 2 has the location, e.g. "Birmingham Academy"
    location = lines[1]

    rows = []

    for line in lines[2:]:
        line = line.strip()

        if line == "":
            continue  # skip blank lines

        if "Psychometrics" not in line:
            continue  # skip anything that isn't a person line

        # split on "Psychometrics" so we don't need to worry about
        # whether the separator before it is a hyphen or an en-dash
        name_part, rest = line.split("Psychometrics")
        name = name_part.strip(" --")  # trim trailing dash/space, either kind

        scores_text = "Psychometrics" + rest  # e.g. "Psychometrics: 51/100, Presentation: 19/32"
        score_entries = scores_text.split(", ")

        for entry in score_entries:
            assessment_name, score_text = entry.split(":")
            score_text = score_text.strip()  # remove leading space, e.g. " 51/100"

            score, max_score = score_text.split("/")

            rows.append({
                "name": name,
                "date": date_text,
                "location": location,
                "assessment_name": assessment_name.strip(),
                "score": int(score),
                "max_score": int(max_score),
            })

    return rows


def clean_sparta_day_data(raw_df):
    """Turn the raw_sparta_day_data.csv DataFrame (one row per file) into
    a properly structured DataFrame - one row per person, one column per assessment."""

    all_rows = []

    for index, row in raw_df.iterrows():
        parsed_rows = parse_sparta_day_text(row["raw_text"])

        for r in parsed_rows:
            r["source_file"] = row["source_file"]

        all_rows.extend(parsed_rows)

    long_df = pd.DataFrame(all_rows)

    wide_df = long_df.pivot_table(
        index=["name", "date", "location", "source_file"],
        columns="assessment_name",
        values=["score", "max_score"],
        aggfunc="first"
    )
    wide_df.columns = [f"{value}_{assessment}" for value, assessment in wide_df.columns]
    wide_df = wide_df.reset_index()

    return wide_df



if __name__ == "__main__":
    try:
        raw_df = pd.read_csv("raw_sparta_day_data.csv")
        cleaned_df = clean_sparta_day_data(raw_df)

        print(cleaned_df.head())
        print(cleaned_df.shape)

        cleaned_df.to_csv("cleaned_sparta_day_data.csv", index=False)
    
    except Exception as exc:
        print(f"ERROR: talent_txt_clean.py failed - {exc}")
        sys.exit(4)
