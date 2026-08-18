import os
import boto3
import pandas as pd
import json
# CSV from S3 come back as raw text not strings
# So you need StringIO to wrap it in  string so it behaves like a file and pd.read_csv() can interpret it
from io import StringIO
from dotenv import load_dotenv
# Lets us download multiple files at once
from concurrent.futures import ThreadPoolExecutor

 
# Read .env
load_dotenv()

BUCKET = "data608-final-project-135928476890-eu-central-1-an"

#connecting to the S3
def get_s3_client():
    """Create and return an authenticated S3 client using credentials from .env
    service, login credentials'
    """
    return boto3.client( 
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )



def list_files(bucket, prefix):
    """Return a list of file keys (paths) inside a given S3 bucket/folder using the boto3 client controller """
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' not in response:
        return []
    return [obj['Key'] for obj in response['Contents'] if not obj['Key'].endswith('/')]


def read_csv_from_s3(bucket, key):
    """Read a single CSV file from S3 and return it as a pandas DataFrame"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    #needs converting to a string from bytes using utf-8
    csv_content = response['Body'].read().decode('utf-8')
    return pd.read_csv(StringIO(csv_content))


def read_json_from_s3(bucket, key):
    """Read a single JSON file from S3 and return it as a Python dict"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    #same here 
    json_content = response['Body'].read().decode('utf-8')
    return json.loads(json_content)


def parse_academy_filename(key):
    """Pull course, cohort number, and date out of an Academy filename.

    Example: 'Academy/Business_20_2019-02-11.csv'
    -> course='Business', cohort='20', date='2019-02-11'
    """
    # key looks like 'Academy/Business_20_2019-02-11.csv'
    # so, just grab the filename part (after the last '/')
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

    Example: 'Talent/10410.json' 
    """
    filename = key.split('/')[-1]
    talent_id = filename.replace('.json', '')
    return talent_id


def _read_one_academy_file(bucket, key):
    """Download and tag a single Academy file. This is the 'unit of work'
    that we'll run many of at the same time, instead of one after another."""
    df = read_csv_from_s3(bucket, key)


    # bold the three new columns on from the file name onto each row 
    info = parse_academy_filename(key)
    df["course"] = info["course"]
    df["cohort"] = info["cohort"]
    df["date"] = info["date"]

    return df


def load_all_academy_data(bucket=BUCKET, max_workers=10):
    """Read every Academy CSV file from S3, tag each row with its course/
    cohort/date (from the filename), and combine them all into one big
    DataFrame.
    """

    files = list_files(bucket, "Academy/")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # pool.map runs _read_one_academy_file(bucket, key) for every key,
        # but up to max_workers of them are running in parallel at once.
        # It still returns the results in the same order as `files`.
        all_tables = list(
            pool.map(lambda key: _read_one_academy_file(bucket, key), files)
        )

    # stick all the individual file DataFrames together into one
    combined = pd.concat(all_tables, ignore_index=True)
    return combined


def _read_one_talent_file(bucket, key):
    """Download and tag a single Talent file. This is the 'unit of work'
    that we'll run many of at the same time, instead of one after another."""
    record = read_json_from_s3(bucket, key)
    record["talent_id"] = parse_talent_filename(key)
    return record


def load_all_talent_data(bucket=BUCKET, max_workers=10):
    """Read every Talent JSON file from S3, tag each row with its TalentID
    (from the filename), and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    files = list_files(bucket, "Talent/")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        all_rows = list(
            pool.map(lambda key: _read_one_talent_file(bucket, key), files)
        )

    # turns the list of dicts into one DataFrame, one row per person
    combined = pd.DataFrame(all_rows)
    return combined


if __name__ == "__main__":
    academy_df = load_all_academy_data()
    print(academy_df.head())
    print(academy_df.shape)

    talent_df = load_all_talent_data()
    print(talent_df.head())
    print(talent_df.shape)

    academy_df.to_csv("raw_academy_data.csv", index=False)
    talent_df.to_csv("raw_talent_data.csv", index=False)