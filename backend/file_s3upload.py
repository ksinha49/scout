import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def upload_to_s3(file_name, bucket, s3_directory="", object_name=None):
    """Upload a file to an S3 bucket, with an optional directory"""
    s3 = boto3.client('s3')

    # Ensure object_name doesn't include any relative paths
    if object_name is None:
        object_name = os.path.basename(file_name)  # Only use the file name as the S3 key

    # Prepend the S3 directory if provided
    if s3_directory:
        object_name = os.path.join(s3_directory, object_name)

    try:
        s3.upload_file(file_name, bucket, object_name)
        print(f"Upload successful: {file_name} to {bucket}/{object_name}")
    except FileNotFoundError:
        print(f"The file {file_name} was not found")
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except boto3.exceptions.S3UploadFailedError as e:
        print(f"S3 upload failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python file_s3upload.py <file_path> <s3_bucket_name> <s3_directory>")
        sys.exit(1)

    file_path = sys.argv[1]
    bucket_name = sys.argv[2]
    s3_directory = sys.argv[3]

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    # Upload the file to S3 with the specified directory
    upload_to_s3(file_path, bucket_name, s3_directory)
