import os
import boto3
import pandas as pd
import json
from io import StringIO
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

BUCKET = "data608-final-project-135928476890-eu-central-1-an"


log_file = "files_seen.txt"

def load_seen_files():
    """Return the set of S3 keys we've already successfully processed."""
    if not os.path.exists(log_file):
        return set()
    with open(log_file, "r") as file:
        return set(line.strip() for line in file if line.strip())


def mark_files_seen(keys):
    """Append newly-processed keys to the bookmark file so we skip them next run."""
    if not keys:
        return
    with open(log_file, "a") as file:
        for key in keys:
            file.write(key + "\n")

def get_s3_client():
    """Create and return an authenticated S3 client using credentials from .env"""

    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )


# Shared helper function that all data loaders can reuse for dowloading multiple files 
# Using the Thread Pool system with error handling so it doesnt keep looping 
# At failed pulls

def _run_with_error_handling(keys, read_one, max_workers=10):
    """Run read_one(key) across all keys in a thread pool without letting
    one failure kill the batch. Returns (results, succeeded_keys, errors)."""
    results = []
    succeeded_keys = []
    errors = []

    def safe_read(key):
        try:
            return key, read_one(key), None
        except Exception as exc:
            return key, None, str(exc)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for key, result, error in pool.map(safe_read, keys):
            if error is None:
                results.append(result)
                succeeded_keys.append(key)
            else:
                errors.append({"key": key, "error": error})

    return results, succeeded_keys, errors


def list_files(bucket, prefix):
    """Return a list of every file key (path) inside a given S3 bucket/folder.

    S3 only ever gives back up to 1000 files in a single response, even if
    there are more. If there's more, the response includes 'IsTruncated':
    True and a 'NextContinuationToken' we can use to ask for the next
    batch. So we keep asking for more pages, in a loop, until S3 tells us
    there's nothing left."""
    s3 = get_s3_client()

    all_keys = []
    continuation_token = None

    while True:
        if continuation_token:
            response = s3.list_objects_v2(
                Bucket=bucket, Prefix=prefix, ContinuationToken=continuation_token
            )
        else:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' in response:
            for obj in response['Contents']:
                if not obj['Key'].endswith('/'):
                    all_keys.append(obj['Key'])

        # if S3 says there's more, grab the token for the next page and
        # go round the loop again - otherwise we're done
        if response.get('IsTruncated'):
            continuation_token = response['NextContinuationToken']
        else:
            break

    return all_keys

def read_csv_from_s3(bucket, key):
    """Read a single CSV file from S3 and return it as a pandas DataFrame"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    csv_content = response['Body'].read().decode('utf-8')
    return pd.read_csv(StringIO(csv_content))


def read_json_from_s3(bucket, key):
    """Read a single JSON file from S3 and return it as a Python dict"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    json_content = response['Body'].read().decode('utf-8')
    return json.loads(json_content)

def read_txt_from_s3(bucket, key):
    """Read a single JSON file from S3 and return it as a Python dict"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    txt_content = response['Body'].read().decode('utf-8')
    return txt_content


def parse_academy_filename(key):
    """Pull course, cohort number, and date out of an Academy filename.

    Example: 'Academy/Business_20_2019-02-11.csv'
    -> course='Business', cohort='20', date='2019-02-11'
    """
    # key looks like 'Academy/Business_20_2019-02-11.csv'
    # first, just grab the filename part (after the last '/')
    filename = key.split('/')[-1]

    # remove the '.csv' at the end
    filename = filename.replace('.csv', '')

    # now split on the underscores: ['Business', '20', '2019-02-11']
    parts = filename.split('_')

    course = parts[0]
    cohort = parts[1]
    date = parts[2]

    return {"course": course, "cohort": cohort, "date": date}


def parse_talent_filename(key):
    """Pull the TalentID out of a Talent filename.

    Example: 'Talent/10410.json' -> talent_id='10410'
    """
    filename = key.split('/')[-1]
    talent_id = filename.replace('.json', '')
    return talent_id


def _read_one_academy_file(bucket, key):
    """Download and tag a single Academy file. This is the 'unit of work'
    that we'll run many of at the same time, instead of one after another."""
    df = read_csv_from_s3(bucket, key)

    info = parse_academy_filename(key)
    df["course"] = info["course"]
    df["cohort"] = info["cohort"]
    df["date"] = info["date"]

    return df

def _read_one_talent_file(bucket, key):
    """Download and tag a single Talent file. This is the 'unit of work'
    that we'll run many of at the same time, instead of one after another."""
    record = read_json_from_s3(bucket, key)
    record["talent_id"] = parse_talent_filename(key)
    return record


def load_all_academy_data(bucket=BUCKET, max_workers=10):
    seen = load_seen_files()
    all_files = list_files(bucket, "Academy/")
    files = [key for key in all_files if key not in seen]

    if not files:
        print("No new Academy files to process")
        return pd.DataFrame(), []

    tables, succeeded, errors = _run_with_error_handling(
        files, lambda key: _read_one_academy_file(bucket, key), max_workers
    )

    combined = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    mark_files_seen(succeeded)

    return combined, errors



def load_all_talent_data(bucket=BUCKET, max_workers=10):
    """Read every Talent JSON file from S3, tag each row with its TalentID
    (from the filename), and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    seen = load_seen_files()
    all_files = list_files(bucket, "Talent/")
    files = [key for key in all_files if key.endswith(".json") and key not in seen]

    if not files:
        print("No new Talent JSON files to process")
        return pd.DataFrame(), []

    rows, succeeded, errors = _run_with_error_handling(
        files, lambda key: _read_one_talent_file(bucket, key), max_workers
    )

    combined = pd.DataFrame(rows) if rows else pd.DataFrame()
    mark_files_seen(succeeded)

    return combined, errors



def load_all_applicant_talent_data(bucket=BUCKET, max_workers=10):
    """Read every Talent csv file from S3, tag each row with its source
    file, and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    seen = load_seen_files()
    all_files = list_files(bucket, "Talent/")
    files = [
        key for key in all_files
        if key.endswith("Applicants.csv") and key not in seen
    ]

    if not files:
        print("No new Talent application CSV files to process")
        return pd.DataFrame(), []

    def read_one(key):
        df = read_csv_from_s3(bucket, key)
        df["source_file"] = key.split("/")[-1]
        return df

    tables, succeeded, errors = _run_with_error_handling(files, read_one, max_workers)

    combined = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    mark_files_seen(succeeded)

    return combined, errors


def load_all_sparta_day_data(bucket=BUCKET, max_workers=10):
    """Read every Sparta Day txt file from S3, tag each row with its source
    file, and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    seen = load_seen_files()
    all_files = list_files(bucket, "Talent/")
    files = [key for key in all_files if key.endswith(".txt") and key not in seen]

    if not files:
        print("No new Sparta Day txt files to process")
        return pd.DataFrame(), []

    def read_one(key):
        text = read_txt_from_s3(bucket, key)
        return {"source_file": key.split("/")[-1], "raw_text": text}

    rows, succeeded, errors = _run_with_error_handling(files, read_one, max_workers)

    combined = pd.DataFrame(rows) if rows else pd.DataFrame()
    mark_files_seen(succeeded)

    return combined, errors
    
def _append_to_csv(df, path):
    """Append new rows to an existing raw CSV (or create it if this is the
    first run), so incremental runs don't wipe out previously-collected
    data - only writes the header if the file doesn't already exist."""
    if df.empty:
        return
    file_exists = os.path.exists(path)
    df.to_csv(path, mode="a" if file_exists else "w", header=not file_exists, index=False)


if __name__ == "__main__":
    academy_df, academy_errors = load_all_academy_data()
    print(academy_df.head())
    print(academy_df.shape)
    if academy_errors:
        print(f"{len(academy_errors)} Academy file(s) failed:", academy_errors)

    # talent_df = load_all_talent_data()
    # print(talent_df.head())
    # print(talent_df.shape)

    talent_df_csv, applicant_errors = load_all_applicant_talent_data()
    print(talent_df_csv.head())
    print(talent_df_csv.shape)
    if applicant_errors:
        print(f"{len(applicant_errors)} Talent application file(s) failed:", applicant_errors)

    talent_df_txt, sparta_day_errors = load_all_sparta_day_data()
    print(talent_df_txt.head())
    print(talent_df_txt.shape)
    if sparta_day_errors:
        print(f"{len(sparta_day_errors)} Sparta Day file(s) failed:", sparta_day_errors)

    # append the new rows (but tagged) onto the raw CSVs, so we build up a
    # local copy over time without re-downloading from S3 every time
    _append_to_csv(talent_df_csv, "raw_applications_data.csv")
    _append_to_csv(academy_df, "raw_academy_data.csv")
    _append_to_csv(talent_df_txt, "raw_sparta_day_data.csv")
    # talent_df.to_csv("raw_talent_data.csv", index=False)
    print("Saved raw_academy_data.csv, raw_applications_data.csv, and raw_sparta_day_data.csv")
