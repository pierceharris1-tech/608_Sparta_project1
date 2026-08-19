import os
import boto3
import pandas as pd
import json
from io import StringIO
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

BUCKET = "data608-final-project-135928476890-eu-central-1-an"


def get_s3_client():
    """Create and return an authenticated S3 client using credentials from .env"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )


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


def load_all_academy_data(bucket=BUCKET, max_workers=10):
    """Read every Academy CSV file from S3, tag each row with its course/
    cohort/date (from the filename), and combine them all into one big
    DataFrame.

    Instead of downloading one file, waiting for it to finish, then
    downloading the next (slow - most of the time is just waiting on the
    network), we open up several downloads at once using a thread pool.
    Think of it like having multiple checkout lines open instead of one."""

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

'''
def _read_one_talent_file(bucket, key):
    """Download and tag a single Talent file. This is the 'unit of work'
    that we'll run many of at the same time, instead of one after another."""
    record = read_json_from_s3(bucket, key)
    record["talent_id"] = parse_talent_filename(key)
    return record
'''
'''
def load_all_talent_data(bucket=BUCKET, max_workers=10):
    """Read every Talent JSON file from S3, tag each row with its TalentID
    (from the filename), and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    all_files = list_files(bucket, "Talent/")

    files = [key for key in all_files if key.endswith(".json")]

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        all_rows = list(
            pool.map(lambda key: _read_one_talent_file(bucket, key), files)
        )

    # turn our list of dicts into one DataFrame, one row per person
    combined = pd.DataFrame(all_rows)
    return combined

'''
def load_all_applicant_talent_data(bucket=BUCKET, max_workers=10):
    """Read every Talent csv file from S3, tag each row with its cohort
    (from the filename), and combine them all into one big DataFrame.

    Same idea as load_all_academy_data: run several downloads at once
    instead of one at a time."""

    all_files = list_files(bucket, "Talent/")

    csv_files = [key for key in all_files if key.endswith("Applicants.csv")]

    def read_one(key):
        df = read_csv_from_s3(bucket, key)
        df["source_file"] = key.split("/")[-1]
        return df

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        all_tables = list(
            pool.map(read_one, csv_files)
        )

    # turn our list of dicts into one DataFrame, one row per person
    combined = pd.concat(all_tables, ignore_index=True)
    return combined


def load_all_sparta_day_data(bucket=BUCKET, max_workers=10):

    all_files = list_files(bucket, "Talent/")
    
    txt_files = [key for key in all_files if key.endswith(".txt")]

    def read_one(key):
        text = read_txt_from_s3(bucket, key)
        return {"source_file": key.split("/")[-1], "raw_text": text}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        all_rows = list(
            pool.map(read_one, txt_files)
        )

    # turn our list of dicts into one DataFrame, one row per person
    combined = pd.DataFrame(all_rows)
    return combined
    
if __name__ == "__main__":
    academy_df = load_all_academy_data()
    print(academy_df.head())
    print(academy_df.shape)

    # talent_df = load_all_talent_data()
    # print(talent_df.head())
    # print(talent_df.shape)

    talent_df_csv = load_all_applicant_talent_data()
    print(talent_df_csv.head())
    print(talent_df_csv.shape)

    talent_df_txt = load_all_sparta_day_data()
    print(talent_df_txt.head())
    print(talent_df_txt.shape)

    # save both raw (but tagged) tables out as CSV files, so we have a
    # local copy to work from without re-downloading from S3 every time
    talent_df_csv.to_csv("raw_applications_data.csv", index=False)
    academy_df.to_csv("raw_academy_data.csv", index=False)
    talent_df_txt.to_csv("raw_sparta_day_data.csv", index=False)
    # talent_df.to_csv("raw_talent_data.csv", index=False)
    print("Saved raw_academy_data.csv and raw_talent_data.csv")
