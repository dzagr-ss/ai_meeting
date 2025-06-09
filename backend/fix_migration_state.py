#!/usr/bin/env python3
"""
Script to fix migration state when migrations were applied manually
but alembic_version table wasn't updated.
"""

import os
import sys
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from backend.config import get_settings

def fix_migration_state():
    """Stamp the database to the current migration state and fix data"""
    try:
        # Get database URL from settings
        settings = get_settings()
        
        # Create database engine with autocommit
        engine = create_engine(settings.DATABASE_URL)
        
        print("🔧 Fixing existing user data...")
        
        # Set default user_type for existing users who have NULL values
        with engine.begin() as conn:  # Use begin() for auto-commit transaction
            result = conn.execute(text("UPDATE users SET user_type = 'NORMAL' WHERE user_type IS NULL"))
            print(f"✅ Updated {result.rowcount} users with default user_type")
        
        # Also check current state
        with engine.connect() as conn:
            count_result = conn.execute(text("SELECT COUNT(*) FROM users WHERE user_type IS NULL"))
            null_count = count_result.scalar()
            print(f"📊 Users with NULL user_type after update: {null_count}")
            
            total_result = conn.execute(text("SELECT COUNT(*) FROM users"))
            total_count = total_result.scalar()
            print(f"📊 Total users in database: {total_count}")
        
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Get the latest migration revision
        latest_revision = "c9c139249b48"  # Our latest migration
        
        print(f"📋 Stamping database to revision: {latest_revision}")
        
        # Stamp the database to mark migrations as applied
        command.stamp(alembic_cfg, latest_revision)
        
        print("✅ Migration state fixed successfully!")
        print("Database is now marked as up-to-date.")
        
    except Exception as e:
        print(f"❌ Error fixing migration state: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fix_migration_state() 