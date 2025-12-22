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