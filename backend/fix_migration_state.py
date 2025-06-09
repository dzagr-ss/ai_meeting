#!/usr/bin/env python3
"""
Script to fix migration state when migrations were applied manually
but alembic_version table wasn't updated.
"""

import os
import sys
from alembic.config import Config
from alembic import command

def fix_migration_state():
    """Stamp the database to the current migration state"""
    try:
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Get the latest migration revision
        latest_revision = "c9c139249b48"  # Our latest migration
        
        print(f"Stamping database to revision: {latest_revision}")
        
        # Stamp the database to mark migrations as applied
        command.stamp(alembic_cfg, latest_revision)
        
        print("✅ Migration state fixed successfully!")
        print("Database is now marked as up-to-date.")
        
    except Exception as e:
        print(f"❌ Error fixing migration state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_migration_state() 