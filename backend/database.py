from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config import settings
import logging
import time

# Configure database logging
db_logger = logging.getLogger('database')
db_logger.setLevel(logging.INFO)

# Database URL with security considerations
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Enhanced engine configuration with security features
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # Simple configuration for SQLite (local development)
    engine_config = {
        "echo": False,
        "connect_args": {"check_same_thread": False}
    }
else:
    # Full configuration for PostgreSQL (production)
    engine_config = {
        "echo": False,
        "pool_pre_ping": True,
        "pool_recycle": 1800,  # Reduced from 3600 for Railway
        "poolclass": QueuePool,
        "pool_size": 3,        # Reduced from 10 for Railway
        "max_overflow": 5,     # Reduced from 20 for Railway
        "pool_timeout": 10,    # Reduced timeout for faster failover
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "meeting-transcription-app"
        }
    }

# Add SSL configuration for PostgreSQL if in production
if "postgresql" in SQLALCHEMY_DATABASE_URL and "@localhost" not in SQLALCHEMY_DATABASE_URL and "sslmode=disable" not in SQLALCHEMY_DATABASE_URL:
    engine_config["connect_args"].update({
        "sslmode": "require",
        "sslcert": settings.DB_SSL_CERT if hasattr(settings, 'DB_SSL_CERT') else None,
        "sslkey": settings.DB_SSL_KEY if hasattr(settings, 'DB_SSL_KEY') else None,
        "sslrootcert": settings.DB_SSL_ROOT_CERT if hasattr(settings, 'DB_SSL_ROOT_CERT') else None,
    })

# Create engine with security configuration
engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_config)

# Add query logging for security monitoring
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()
    # Log potentially dangerous queries - be more specific to avoid false positives
    statement_upper = statement.upper().strip()
    
    # Only flag truly dangerous operations, not legitimate business operations
    dangerous_patterns = [
        'DROP ',
        'TRUNCATE ',
        'ALTER ',
        'CREATE ',
        'GRANT ',
        'REVOKE ',
    ]
    
    # Check for dangerous user table modifications (but allow other table operations)
    user_table_patterns = [
        'INSERT INTO users',
        'UPDATE users',
        'DELETE FROM users'
    ]
    
    # Check if the query starts with any dangerous pattern
    is_dangerous = any(statement_upper.startswith(pattern) for pattern in dangerous_patterns)
    
    # Check for user table modifications
    if any(pattern in statement_upper for pattern in user_table_patterns):
        is_dangerous = True
    
    # Check for UPDATE/DELETE without WHERE clause (but exclude legitimate operations)
    if statement_upper.startswith('UPDATE ') or statement_upper.startswith('DELETE FROM '):
        if 'WHERE' not in statement_upper:
            # Allow specific legitimate operations without WHERE clause
            legitimate_operations = [
                'DELETE FROM transcriptions',  # Transcription grouping operations
                'DELETE FROM summaries',       # Summary cleanup operations
                'DELETE FROM meeting_notes'    # Notes cleanup operations
            ]
            
            # Only flag as dangerous if it's not a legitimate operation
            if not any(op in statement_upper for op in legitimate_operations):
                is_dangerous = True
        else:
            # Even with WHERE clause, check for overly broad conditions
            # Allow operations that target specific meeting_id or user_id
            if ('MEETING_ID' in statement_upper or 'USER_ID' in statement_upper or 
                'ID =' in statement_upper or 'ID IN' in statement_upper):
                # These are legitimate targeted operations
                pass
            elif ('WHERE 1=1' in statement_upper or 'WHERE TRUE' in statement_upper):
                # These are dangerous broad operations
                is_dangerous = True
    
    if is_dangerous:
        db_logger.warning(f"Potentially dangerous query executed: {statement[:100]}...")

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    # Log slow queries
    if total > 1.0:  # Log queries taking more than 1 second
        db_logger.warning(f"Slow query detected ({total:.2f}s): {statement[:100]}...")

# Session configuration with security considerations
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

Base = declarative_base()

def get_db():
    """
    Database dependency with proper error handling and logging
    """
    db = SessionLocal()
    try:
        # Test connection
        db.execute("SELECT 1")
        yield db
    except Exception as e:
        db_logger.error(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Database health check function
def check_database_health():
    """Check database connectivity and performance"""
    try:
        db = SessionLocal()
        start_time = time.time()
        db.execute("SELECT 1")
        response_time = time.time() - start_time
        db.close()
        
        if response_time > 5.0:
            db_logger.warning(f"Database response time is slow: {response_time:.2f}s")
            return False
        
        return True
    except Exception as e:
        db_logger.error(f"Database health check failed: {e}")
        return False 