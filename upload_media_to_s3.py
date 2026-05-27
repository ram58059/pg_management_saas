import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'ap-south-1')

def upload_media_to_s3():
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME]):
        print("Missing AWS credentials in .env file.")
        return

    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )

    media_dir = os.path.join(os.path.dirname(__file__), 'media')
    
    if not os.path.exists(media_dir):
        print(f"Media directory not found at {media_dir}")
        return

    count = 0
    for root, dirs, files in os.walk(media_dir):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            local_path = os.path.join(root, file)
            # The S3 key should be relative to the media directory
            # E.g. 'payment_screenshots/2026/05/file.png'
            s3_key = os.path.relpath(local_path, media_dir)
            
            # Determine content type based on extension
            content_type = 'image/png'
            if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            
            print(f"Uploading {local_path} to s3://{AWS_STORAGE_BUCKET_NAME}/{s3_key}")
            try:
                s3_client.upload_file(
                    local_path, 
                    AWS_STORAGE_BUCKET_NAME, 
                    s3_key,
                    ExtraArgs={'ContentType': content_type}
                )
                print(f"✓ Successfully uploaded {s3_key}")
                count += 1
            except Exception as e:
                print(f"✗ Failed to upload {s3_key}: {str(e)}")

    print(f"\nCompleted! Uploaded {count} files to S3.")

if __name__ == '__main__':
    upload_media_to_s3()
