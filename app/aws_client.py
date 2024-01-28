import boto3

from app.config import config

sns_client = boto3.client(
    'sns',
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
    region_name='us-east-1',
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=config['S3_ACCESS_KEY_ID'],
    aws_secret_access_key=config['S3_SECRET_ACCESS_KEY'],
    region_name='ap-northeast-2',
)
