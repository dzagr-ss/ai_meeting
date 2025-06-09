import psycopg2
import os

try:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    
    # Check if alembic_version table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        );
    """)
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        cur.execute("SELECT version_num FROM alembic_version;")
        result = cur.fetchone()
        print(f"Current migration: {result[0] if result else 'No migration applied'}")
    else:
        print("No alembic_version table found - database not initialized")
    
    # Also check if users table has user_type column
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'user_type';
    """)
    user_type_exists = cur.fetchone()
    print(f"user_type column exists: {bool(user_type_exists)}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close() 