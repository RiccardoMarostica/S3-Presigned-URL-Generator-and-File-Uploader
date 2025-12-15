# S3 Presigned URL Generator and File Uploader

A Python utility for generating S3 presigned URLs and uploading files to Amazon S3 using presigned POST URLs. This tool provides both upload functionality and download URL generation through a simple command-line interface.

## Features

- **File Upload**: Upload files to S3 using presigned POST URLs
- **Download URL Generation**: Generate presigned GET URLs for downloading S3 objects
- **Command-Line Interface**: Easy-to-use CLI with comprehensive options
- **AWS Profile Support**: Use different AWS profiles for authentication
- **Configurable Expiration**: Set custom expiration times for presigned URLs
- **Robust Error Handling**: Comprehensive error handling and logging
- **Type Safety**: Full type hints for better code maintainability

## Prerequisites

- Python 3.7+
- AWS CLI configured with appropriate credentials
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure your AWS credentials are configured (via AWS CLI, environment variables, or IAM roles)

## Usage

The tool supports two main operations: `post` (upload) and `get` (download URL generation).

### Upload Files (POST Operation)

Upload a file to S3 and get the resulting S3 object key:

```bash
# Basic upload
python app.py post --bucket my-bucket --file image.jpg

# Upload with custom S3 object key
python app.py post --bucket my-bucket --file image.jpg --key images/my-image.jpg

# Upload with custom expiration (2 hours)
python app.py post --bucket my-bucket --file image.jpg --expiration 7200
```

**Output:**
```
SUCCESS: File uploaded to S3
S3 Object Key: image.jpg
S3 URI: s3://my-bucket/image.jpg
```

### Generate Download URLs (GET Operation)

Generate a presigned URL for downloading an S3 object:

```bash
# Generate download URL
python app.py get --bucket my-bucket --key image.jpg

# Generate URL with custom expiration
python app.py get --bucket my-bucket --key images/my-image.jpg --expiration 3600
```

**Output:**
```
SUCCESS: Presigned GET URL generated
URL: https://my-bucket.s3.amazonaws.com/image.jpg?AWSAccessKeyId=...
Expires in: 3600 seconds
```

## Command-Line Options

### Global Options
- `--profile, -p`: AWS profile name (default: `default`)

### POST Operation Options
- `--bucket, -b`: S3 bucket name (required)
- `--file, -f`: File path to upload (required)
- `--key, -k`: S3 object key (optional, defaults to filename)
- `--expiration, -e`: URL expiration time in seconds (default: 3600)

### GET Operation Options
- `--bucket, -b`: S3 bucket name (required)
- `--key, -k`: S3 object key (required)
- `--expiration, -e`: URL expiration time in seconds (default: 3600)

## Examples

```bash
# Upload test-1.jpg to my-bucket bucket
python app.py post --bucket my-bucket --file test-1.jpg

# Upload with organized folder structure
python app.py post --bucket my-bucket --file photo.jpg --key uploads/2024/photo.jpg

# Generate download link for existing file
python app.py get --bucket my-bucket --key test-1.jpg

# Use different AWS profile
python app.py post --bucket my-bucket --file image.jpg --profile production

# Set 24-hour expiration
python app.py get --bucket my-bucket --key document.pdf --expiration 86400
```

## AWS Permissions Required

Your AWS credentials need the following S3 permissions:

For POST operations:
- `s3:PutObject` on the target bucket/objects
- `s3:PutObjectAcl` (if using ACL conditions)

For GET operations:
- `s3:GetObject` on the target bucket/objects

## Error Handling

The tool provides comprehensive error handling for common scenarios:

- **AWS Configuration Issues**: Missing profiles, invalid credentials
- **File System Errors**: File not found, permission issues
- **Network Errors**: Connection timeouts, request failures
- **S3 Errors**: Bucket access denied, object not found

All errors are logged with detailed information to help with troubleshooting.

## Logging

The application uses structured logging with timestamps. Log levels include:
- **INFO**: Successful operations and progress updates
- **ERROR**: Failed operations with detailed error information

## Security Considerations

- Presigned URLs provide temporary access to S3 objects
- Default expiration is 1 hour (3600 seconds)
- URLs should be treated as sensitive and not shared publicly beyond their intended use
- Consider using shorter expiration times for sensitive content

## License

This project is provided as-is for educational and development purposes.