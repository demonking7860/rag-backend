# Enabling Temporary Public Access for RDS (Testing Only)

⚠️ **SECURITY WARNING**: This should ONLY be used for development/testing. Never enable public access in production!

## Step-by-Step Instructions

### Step 1: Enable Public Access in RDS Console

1. **Go to AWS RDS Console**
   - Navigate to: https://console.aws.amazon.com/rds/
   - Make sure you're in the correct region (us-east-1)

2. **Select Your Database Instance**
   - Click on your database instance: `database-1`
   - Or search for it in the list

3. **Modify the Database Instance**
   - Click the **"Modify"** button (top right)

4. **Enable Public Access**
   - Scroll down to **"Connectivity"** section
   - Find **"Public access"** setting
   - Change it from **"No"** to **"Yes"**
   - ⚠️ This will make your database accessible from the internet

5. **Apply Changes**
   - Scroll to the bottom
   - Choose **"Apply immediately"** (or schedule for next maintenance window)
   - Click **"Modify DB instance"**
   - Wait for the modification to complete (usually 2-5 minutes)

### Step 2: Configure Security Group

Your RDS security group (`sg-0032639d52dc7bf05`) needs to allow inbound connections from your IP address.

1. **Go to EC2 Console → Security Groups**
   - Navigate to: https://console.aws.amazon.com/ec2/
   - Click on **"Security Groups"** in the left sidebar

2. **Find Your RDS Security Group**
   - Search for: `sg-0032639d52dc7bf05`
   - Or look for the security group named `default` that's attached to your RDS instance

3. **Add Inbound Rule**
   - Select the security group
   - Click on **"Inbound rules"** tab
   - Click **"Edit inbound rules"**

4. **Add PostgreSQL Rule**
   - Click **"Add rule"**
   - **Type**: PostgreSQL (or Custom TCP)
   - **Port**: 5432
   - **Source**: Choose one of:
     - **My IP**: Automatically uses your current IP (recommended)
     - **Custom**: Enter your specific IP address (e.g., `203.0.113.0/32`)
     - ⚠️ **DO NOT** use `0.0.0.0/0` (allows access from anywhere - very insecure!)
   - **Description**: "Temporary access for testing"
   - Click **"Save rules"**

### Step 3: Find Your Public IP Address

If you chose "Custom" in Step 2, you need to know your public IP:

**Option A: Check in AWS Console**
- When adding the security group rule, AWS shows "My IP" with your current IP

**Option B: Use a website**
- Visit: https://whatismyipaddress.com/
- Copy your IPv4 address
- Use format: `YOUR_IP/32` (e.g., `203.0.113.45/32`)

### Step 4: Test Connection

Once the RDS modification is complete and security group is updated:

1. **Test from command line** (if you have psql installed):
   ```bash
   psql -h database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com \
        -p 5432 \
        -U postgres \
        -d postgres
   ```
   - Enter password when prompted: `dASQf_XQV3>6x64N9oKJVzXpL9-u`

2. **Test with Django**:
   ```bash
   cd backend
   python config/test_secrets.py
   ```

3. **Run Django migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Install pgvector extension**:
   ```sql
   -- Connect to database and run:
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### Step 5: IMPORTANT - Disable Public Access After Testing

⚠️ **CRITICAL**: Remember to disable public access when done testing!

1. **Go back to RDS Console**
   - Select your database instance
   - Click **"Modify"**

2. **Disable Public Access**
   - Scroll to **"Connectivity"** section
   - Change **"Public access"** from **"Yes"** back to **"No"**
   - Click **"Modify DB instance"**

3. **Remove Security Group Rule** (Optional but recommended)
   - Go to EC2 → Security Groups
   - Select your RDS security group
   - Edit inbound rules
   - Remove the temporary PostgreSQL rule you added
   - Save rules

## Troubleshooting

### Connection Timeout
- **Check**: Security group rule is correct and your IP is allowed
- **Check**: RDS modification has completed (check status in console)
- **Check**: Your IP address hasn't changed (if using dynamic IP)

### Authentication Failed
- **Check**: Username is `postgres`
- **Check**: Password is correct: `dASQf_XQV3>6x64N9oKJVzXpL9-u`
- **Check**: Database name is `postgres`

### "Publicly accessible modification is currently not supported"
- This can happen if the instance is in a certain state
- Wait a few minutes and try again
- Make sure no other modifications are in progress

## Security Best Practices

1. ✅ **Use specific IP addresses** - Never use `0.0.0.0/0`
2. ✅ **Remove rules after testing** - Clean up security group rules
3. ✅ **Disable public access** - Turn it off when not needed
4. ✅ **Use strong passwords** - Your RDS password is already strong
5. ✅ **Monitor access logs** - Check CloudWatch for suspicious activity
6. ✅ **Use VPN/Bastion for production** - Never use public access in production

## Alternative: Quick Test Script

Create a file `test_rds_connection.py`:

```python
import psycopg2
from urllib.parse import quote_plus

# Your credentials
host = "database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com"
port = 5432
username = "postgres"
password = "dASQf_XQV3>6x64N9oKJVzXpL9-u"
database = "postgres"

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        connect_timeout=10
    )
    print("✅ Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"PostgreSQL version: {version}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
```

Run it:
```bash
pip install psycopg2-binary
python test_rds_connection.py
```

