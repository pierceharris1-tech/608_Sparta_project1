import os
import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET = "data-608-clean-data"

CLEANED_FILES = {
    "cleaned_academy_data.csv": "data/cleaned_academy_data.csv",
    "clean_talent_data.csv": "data/clean_talent_data.csv",
    "clean_talent_applications_data_updated.csv": "data/clean_talent_applications_data.csv",
    "cleaned_sparta_day_data.csv": "data/cleaned_sparta_day_data.csv",
}


def get_s3_client():
    """Create and return an authenticated S3 client using credentials from .env"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )


def upload_cleaned_data(bucket=BUCKET, files=CLEANED_FILES):
    """Upload each cleaned CSV to the clean-data S3 bucket. Skips any file
    that doesn't exist locally and keeps going if one upload fails, instead
    of stopping the whole batch."""
    s3 = get_s3_client()

    for local_path, key in files.items():
        if not os.path.exists(local_path):
            print(f"Skipping {local_path} - file not found")
            continue

        try:
            s3.upload_file(Filename=local_path, Bucket=bucket, Key=key)
            print(f"Uploaded {local_path} -> s3://{bucket}/{key}")
        except Exception as exc:
            print(f"Failed to upload {local_path}: {exc}")


if __name__ == "__main__":
    upload_cleaned_data()
