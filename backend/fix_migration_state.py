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
        
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        print("🔧 Fixing existing user data...")
        
        # Set default user_type for existing users who have NULL values
        with engine.connect() as conn:
            result = conn.execute(text("UPDATE users SET user_type = 'NORMAL' WHERE user_type IS NULL"))
            conn.commit()
            print(f"✅ Updated {result.rowcount} users with default user_type")
        
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
        sys.exit(1)

if __name__ == "__main__":
    fix_migration_state() 