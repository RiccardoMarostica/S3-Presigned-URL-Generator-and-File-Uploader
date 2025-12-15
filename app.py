import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class S3PresignedUploader:
    """Handle S3 presigned URL generation and file uploads."""
    
    def __init__(self, profile_name: str = 'default'):
        """Initialize the S3 client with the specified AWS profile.
        
        Args:
            profile_name: AWS profile name to use for authentication
            
        Raises:
            ProfileNotFound: If the specified AWS profile doesn't exist
            NoCredentialsError: If AWS credentials are not configured
        """
        try:
            self.session = boto3.Session(profile_name=profile_name)
            self.s3_client = self.session.client('s3')
            logger.info(f"Successfully initialized S3 client with profile: {profile_name}")
        except ProfileNotFound:
            logger.error(f"AWS profile '{profile_name}' not found")
            raise
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise

    def create_presigned_post(
        self,
        bucket_name: str,
        object_name: str,
        fields: Optional[Dict[str, str]] = None,
        conditions: Optional[List[Any]] = None,
        expiration: int = 3600
    ) -> Optional[Dict[str, Any]]:
        """Generate a presigned URL for S3 POST request to upload a file.

        Args:
            bucket_name: S3 bucket name
            object_name: S3 object name (key)
            fields: Dictionary of prefilled form fields
            conditions: List of conditions to include in the policy
            expiration: Time in seconds for the presigned URL to remain valid

        Returns:
            Dictionary with 'url' and 'fields' keys, or None if error occurs
        """
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=bucket_name,
                Key=object_name,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration,
            )
            logger.info(f"Successfully generated presigned URL for {object_name}")
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Failed to generate presigned URL: {error_code} - {e}")
            return None

    def create_presigned_get_url(
        self,
        bucket_name: str,
        object_name: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """Generate a presigned URL for S3 GET request to download a file.

        Args:
            bucket_name: S3 bucket name
            object_name: S3 object name (key)
            expiration: Time in seconds for the presigned URL to remain valid

        Returns:
            Presigned URL string, or None if error occurs
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            logger.info(f"Successfully generated presigned GET URL for {object_name}")
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Failed to generate presigned GET URL: {error_code} - {e}")
            return None

    def upload_file_with_presigned_url(
        self,
        file_path: str,
        bucket_name: str,
        object_name: Optional[str] = None,
        expiration: int = 3600
    ) -> bool:
        """Upload a file using a presigned URL.

        Args:
            file_path: Path to the file to upload
            bucket_name: S3 bucket name
            object_name: S3 object name (defaults to filename)
            expiration: Time in seconds for the presigned URL to remain valid

        Returns:
            True if upload successful, False otherwise
        """
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        # Use filename as object name if not specified
        if object_name is None:
            object_name = file_path.name
            
        logger.info(f"Starting upload of {file_path} to s3://{bucket_name}/{object_name}")
        
        # Generate presigned URL
        presigned_data = self.create_presigned_post(
            bucket_name=bucket_name,
            object_name=object_name,
            expiration=expiration
        )
        
        if presigned_data is None:
            logger.error("Failed to generate presigned URL")
            return False
            
        # Upload file
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (object_name, f)}
                response = requests.post(
                    presigned_data['url'],
                    data=presigned_data['fields'],
                    files=files,
                    timeout=30
                )
                
            # Check if upload was successful (S3 returns 204 for successful uploads)
            if response.status_code == 204:
                logger.info(f"Successfully uploaded {file_path} (HTTP {response.status_code})")
                return True
            else:
                logger.error(f"Upload failed with HTTP status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during upload: {e}")
            return False
        except IOError as e:
            logger.error(f"File I/O error: {e}")
            return False

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='S3 Presigned URL Generator and File Uploader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a file and get the S3 object key
  python app.py post --bucket my-bucket --file image.jpg

  # Generate a presigned GET URL for downloading
  python app.py get --bucket my-bucket --key path/to/image.jpg

  # Upload with custom expiration time (2 hours)
  python app.py post --bucket my-bucket --file image.jpg --expiration 7200
        """
    )
    
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')
    subparsers.required = True
    
    # POST operation (upload)
    post_parser = subparsers.add_parser('post', help='Upload file using presigned POST URL')
    post_parser.add_argument('--bucket', '-b', required=True, help='S3 bucket name')
    post_parser.add_argument('--file', '-f', required=True, help='File path to upload')
    post_parser.add_argument('--key', '-k', help='S3 object key (defaults to filename)')
    post_parser.add_argument('--expiration', '-e', type=int, default=3600, 
                           help='URL expiration time in seconds (default: 3600)')
    
    # GET operation (download URL)
    get_parser = subparsers.add_parser('get', help='Generate presigned GET URL for downloading')
    get_parser.add_argument('--bucket', '-b', required=True, help='S3 bucket name')
    get_parser.add_argument('--key', '-k', required=True, help='S3 object key')
    get_parser.add_argument('--expiration', '-e', type=int, default=3600,
                          help='URL expiration time in seconds (default: 3600)')
    
    parser.add_argument('--profile', '-p', default='lab4', help='AWS profile name (default: lab4)')
    
    return parser

def handle_post_operation(args, uploader: S3PresignedUploader) -> None:
    """Handle POST operation (file upload)."""
    file_path = Path(args.file)
    object_key = args.key if args.key else file_path.name
    
    logger.info(f"POST operation: Uploading {args.file} to s3://{args.bucket}/{object_key}")
    
    success = uploader.upload_file_with_presigned_url(
        file_path=args.file,
        bucket_name=args.bucket,
        object_name=object_key,
        expiration=args.expiration
    )
    
    if success:
        print(f"SUCCESS: File uploaded to S3")
        print(f"S3 Object Key: {object_key}")
        print(f"S3 URI: s3://{args.bucket}/{object_key}")
    else:
        logger.error("File upload failed")
        sys.exit(1)

def handle_get_operation(args, uploader: S3PresignedUploader) -> None:
    """Handle GET operation (generate download URL)."""
    logger.info(f"GET operation: Generating presigned URL for s3://{args.bucket}/{args.key}")
    
    presigned_url = uploader.create_presigned_get_url(
        bucket_name=args.bucket,
        object_name=args.key,
        expiration=args.expiration
    )
    
    if presigned_url:
        print(f"SUCCESS: Presigned GET URL generated")
        print(f"URL: {presigned_url}")
        print(f"Expires in: {args.expiration} seconds")
    else:
        logger.error("Failed to generate presigned GET URL")
        sys.exit(1)

def main():
    """Main function with command-line argument handling."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Initialize uploader
        uploader = S3PresignedUploader(profile_name=args.profile)
        
        # Handle operations
        if args.operation == 'post':
            handle_post_operation(args, uploader)
        elif args.operation == 'get':
            handle_get_operation(args, uploader)
            
    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()