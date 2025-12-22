# S3 Bucket Policy Configuration

## Recommended Policy for Pre-Signed URL Uploads

This policy allows pre-signed URL uploads while keeping your bucket private.

1. Go to AWS S3 Console → Your bucket (`rag-testing8756`)
2. **Permissions** tab → **Bucket policy** → **Edit**
3. Add this policy (replace `YOUR_ACCOUNT_ID` with your AWS account ID):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPreSignedURLUploads",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::rag-testing8756/uploads/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        },
        {
            "Sid": "DenyPublicAccess",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::rag-testing8756/*",
            "Condition": {
                "Bool": {
                    "aws:ViaAWSService": "false"
                }
            }
        }
    ]
}
```

## Simpler Policy (If Above Doesn't Work)

If you need a simpler policy that allows pre-signed uploads:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPreSignedUploads",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::rag-testing8756/uploads/*"
        }
    ]
}
```

**Note:** Pre-signed URLs already handle authentication, so the bucket policy mainly needs to allow PutObject operations.

## Important: Keep Block Public Access ON

- **Block Public Access** should remain **ON** (default)
- Pre-signed URLs work with private buckets
- Only the pre-signed URL holder can upload during the validity period

