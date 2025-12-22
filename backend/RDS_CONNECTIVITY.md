# RDS Connectivity Guide

## Your RDS Configuration

- **Endpoint**: `database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com`
- **Port**: `5432`
- **VPC**: `vpc-0dee4b2f9bda87f2c`
- **Publicly Accessible**: No (Recommended for security)

## Connectivity Options

Since your RDS instance is **not publicly accessible**, you have several options to connect:

### Option 1: EC2 Instance in Same VPC (Recommended for Production)

1. Launch an EC2 instance in the same VPC (`vpc-0dee4b2f9bda87f2c`)
2. Ensure the security group allows outbound connections to port 5432
3. Update the RDS security group to allow inbound connections from your EC2 security group
4. Deploy your Django application on the EC2 instance

**Security Group Rules Needed:**
- RDS Security Group (`sg-0032639d52dc7bf05`): Allow inbound port 5432 from EC2 security group
- EC2 Security Group: Allow outbound port 5432 to RDS security group

### Option 2: AWS Systems Manager Session Manager (For Local Development)

Use AWS Systems Manager Session Manager to create a secure tunnel:

```bash
# Install AWS CLI and Session Manager plugin
# Then create a port forwarding session:
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["5432"],"localPortNumber":["5432"]}'
```

Then connect to `localhost:5432` from your local machine.

### Option 3: VPN Connection

1. Set up a VPN (AWS Client VPN or third-party)
2. Connect your local machine to the VPN
3. Your Django app can then connect to the RDS endpoint

### Option 4: Bastion Host (Jump Server)

1. Launch a small EC2 instance in the same VPC
2. Configure SSH tunneling:
   ```bash
   ssh -L 5432:database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com:5432 ec2-user@bastion-host
   ```
3. Connect to `localhost:5432` from your local machine

### Option 5: Temporarily Enable Public Access (NOT Recommended for Production)

⚠️ **Security Warning**: Only use this for development/testing!

See detailed step-by-step instructions in: **`RDS_PUBLIC_ACCESS_GUIDE.md`**

Quick steps:
1. Go to RDS Console → Modify DB Instance → Enable "Publicly accessible"
2. Update security group (`sg-0032639d52dc7bf05`) to allow your IP on port 5432
3. Test connection
4. **CRITICAL: Disable public access after testing!**

## Security Group Configuration

Your RDS security group (`sg-0032639d52dc7bf05`) needs to allow inbound connections:

**For EC2 deployment:**
- Type: PostgreSQL
- Port: 5432
- Source: EC2 Security Group ID

**For VPN/Bastion:**
- Type: PostgreSQL
- Port: 5432
- Source: Your VPN IP range or Bastion IP

## Testing Connection

Once you have connectivity set up, test the connection:

```bash
cd backend
python config/test_secrets.py
```

Or test directly with psql:

```bash
psql -h database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com \
     -p 5432 \
     -U postgres \
     -d postgres
```

## Environment Variables

Your `.env` file should have:

```env
RDS_SECRET_NAME=rds!db-dc867e91-d63e-4af0-ad84-122afa8ff1de
RDS_SECRET_REGION=us-east-1
RDS_DB_HOST=database-1.c2hekoqimvwz.us-east-1.rds.amazonaws.com
RDS_DB_NAME=postgres
```

## Next Steps

1. Choose a connectivity method based on your needs
2. Configure security groups accordingly
3. Test the connection using the test script
4. Run Django migrations: `python manage.py migrate`
5. Install pgvector extension: `CREATE EXTENSION vector;`

