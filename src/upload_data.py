import boto3
from pprint import pprint
import json
import pandas as pd

bucket_name = 'data-608-clean-data'
s3_client = boto3.client('s3')
bucket_list = s3_client.list_buckets()
pprint(bucket_list)


bucket_contents = s3_client.list_objects_v2(Bucket=bucket_name)
pprint(bucket_contents)

s3_resources = boto3.resource('s3')
bucket = s3_resources.Bucket(bucket_name)

# talent = pd.read_csv('clean_talent_data.csv')
# academy = pd.read_csv('raw_academy_data.csv)
# applicants = pd.read_csv('../clean_talent_applications_data.csv')
sparta_day = pd.read_csv('../cleaned_sparta_day_data.csv')

# talent.to_csv('talent.csv', index=False)
# s3_client.upload_file(
#     Filename='talent.csv',
#     Bucket= bucket_name,
#     Key='data/talent.csv',
# )

# academy.to_csv('academy.csv', index=False)
# s3_client.upload_file(
#     Filename='academy.csv',
#     Bucket= bucket_name,
#     Key='data/academy.csv',
# )

sparta_day.to_csv('cleaned_sparta_day_assessments.csv', index=False)
s3_client.upload_file(
    Filename='cleaned_sparta_day_assessments.csv',
    Bucket= bucket_name,
    Key='data/cleaned_sparta_day_assessments.csv',
)