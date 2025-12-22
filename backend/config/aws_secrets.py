"""
AWS Secrets Manager utility for retrieving RDS database credentials.
"""
import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


def get_secret(secret_name: str, region_name: str = 'us-east-1') -> dict:
    """
    Retrieve secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region_name: AWS region where the secret is stored
        
    Returns:
        dict: Secret value as a dictionary
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise
    
    secret_string = get_secret_value_response['SecretString']
    return json.loads(secret_string)


def get_database_url_from_secret(
    secret_name: str,
    region_name: str = 'us-east-1',
    db_host: str = None,
    db_port: int = None,
    db_name: str = None
) -> str:
    """
    Retrieve database credentials from AWS Secrets Manager and construct DATABASE_URL.
    
    RDS secrets typically contain: username, password, host, port, dbname, engine
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region_name: AWS region where the secret is stored
        db_host: RDS endpoint hostname (fallback if not in secret)
        db_port: Database port (fallback if not in secret, default: 5432)
        db_name: Database name (fallback if not in secret)
        
    Returns:
        str: PostgreSQL DATABASE_URL connection string
    """
    secret = get_secret(secret_name, region_name)
    
    # Extract credentials from secret (RDS format)
    username = secret.get('username')
    password = secret.get('password')
    
    # Get database host, port, and name from secret first, then fall back to parameters
    host = secret.get('host') or db_host
    port = secret.get('port') or db_port or 5432
    database = secret.get('dbname') or secret.get('database') or db_name
    
    if not username or not password:
        raise ValueError("Secret must contain 'username' and 'password'")
    
    if not host:
        raise ValueError(
            "Database host must be provided. "
            "Either set RDS_DB_HOST in .env or ensure the secret contains 'host'"
        )
    
    if not database:
        raise ValueError(
            "Database name must be provided. "
            "Either set RDS_DB_NAME in .env or ensure the secret contains 'dbname'"
        )
    
    # Construct DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    # URL-encode password to handle special characters
    from urllib.parse import quote_plus
    encoded_password = quote_plus(password)
    database_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
    
    return database_url

