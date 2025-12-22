# S3 CORS Configuration

## Problem
CORS error when uploading files directly to S3 from frontend.

## Solution: Configure S3 Bucket CORS

**Important:** You need BOTH CORS configuration AND proper bucket permissions. See `S3_BUCKET_POLICY.md` for bucket policy setup.

1. Go to AWS S3 Console
2. Select your bucket: `rag-testing8756`
3. Go to **Permissions** tab
4. Scroll to **Cross-origin resource sharing (CORS)**
5. Click **Edit**
6. Add this CORS configuration:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-server-side-encryption",
            "x-amz-request-id",
            "x-amz-id-2"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

7. Click **Save changes**

## For Production

Update `AllowedOrigins` to your production domain:
```json
"AllowedOrigins": [
    "https://yourdomain.com"
]
```

