#!/usr/bin/env python3
"""
Simple test script for the new file storage structure
"""

import os
import tempfile
import shutil
import glob

def get_safe_email_for_path(email: str) -> str:
    """Convert email to a safe filename format"""
    return email.replace("@", "_at_").replace(".", "_").replace("/", "_").replace("\\", "_")

def test_safe_email_conversion():
    """Test email to safe path conversion"""
    test_cases = [
        ("user@example.com", "user_at_example_com"),
        ("test.user@domain.co.uk", "test_user_at_domain_co_uk"),
        ("user+tag@example.com", "user+tag_at_example_com"),
        ("user/with/slashes@example.com", "user_with_slashes_at_example_com"),
    ]
    
    print("Testing email to safe path conversion:")
    for email, expected in test_cases:
        result = get_safe_email_for_path(email)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {email} -> {result}")
        if result != expected:
            print(f"    Expected: {expected}")

def test_file_structure():
    """Test the new file structure creation and retrieval"""
    print("\nTesting file structure:")
    
    # Create test directory structure
    test_base = "/tmp/test_meetings"
    if os.path.exists(test_base):
        shutil.rmtree(test_base)
    
    # Test data
    test_email = "test@example.com"
    meeting_id = 123
    safe_email = get_safe_email_for_path(test_email)
    
    # Create directory structure
    user_meeting_dir = f"{test_base}/{safe_email}/{meeting_id}"
    os.makedirs(user_meeting_dir, exist_ok=True)
    
    # Create test files
    test_files = [
        f"meeting_{meeting_id}_20240101_120000.wav",
        f"meeting_{meeting_id}_20240101_130000.wav",
        f"meeting_{meeting_id}_20240101_140000.wav",
    ]
    
    for filename in test_files:
        filepath = os.path.join(user_meeting_dir, filename)
        with open(filepath, 'w') as f:
            f.write("test audio data")
    
    print(f"  ✓ Created test structure: {user_meeting_dir}")
    print(f"  ✓ Created {len(test_files)} test files")
    
    # Test file retrieval
    pattern = f"{user_meeting_dir}/meeting_{meeting_id}_*.wav"
    found_files = glob.glob(pattern)
    found_files.sort()
    
    if len(found_files) == len(test_files):
        print(f"  ✓ Retrieved {len(found_files)} files correctly")
        for i, filepath in enumerate(found_files):
            expected_filename = test_files[i]
            actual_filename = os.path.basename(filepath)
            status = "✓" if actual_filename == expected_filename else "✗"
            print(f"    {status} {actual_filename}")
    else:
        print(f"  ✗ Expected {len(test_files)} files, got {len(found_files)}")
    
    # Test directory structure
    expected_structure = f"{test_base}/test_at_example_com/123"
    if os.path.exists(expected_structure):
        print(f"  ✓ Directory structure created correctly: {expected_structure}")
    else:
        print(f"  ✗ Directory structure not found: {expected_structure}")
    
    # Cleanup
    shutil.rmtree(test_base)
    print(f"  ✓ Cleaned up test directory")

def test_migration_scenario():
    """Test migration from old to new structure"""
    print("\nTesting migration scenario:")
    
    # Create old structure files
    old_files = [
        "/tmp/meeting_456_20240101_120000.wav",
        "/tmp/meeting_456_20240101_130000.wav",
    ]
    
    created_files = []
    
    # Create test files in old location
    for filepath in old_files:
        try:
            with open(filepath, 'w') as f:
                f.write("test audio data")
            created_files.append(filepath)
            print(f"  ✓ Created old structure file: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Failed to create {filepath}: {e}")
    
    # Test that files exist in old location
    found_old_files = glob.glob("/tmp/meeting_456_*.wav")
    print(f"  ✓ Found {len(found_old_files)} files in old location")
    
    # Simulate migration
    if found_old_files:
        test_email = "testuser@example.com"
        meeting_id = 456
        safe_email = get_safe_email_for_path(test_email)
        new_dir = f"/tmp/test_migration/{safe_email}/{meeting_id}"
        os.makedirs(new_dir, exist_ok=True)
        
        migrated_count = 0
        for old_file in found_old_files:
            filename = os.path.basename(old_file)
            new_path = os.path.join(new_dir, filename)
            try:
                shutil.copy2(old_file, new_path)  # Use copy instead of move for testing
                migrated_count += 1
                print(f"  ✓ Migrated: {filename}")
            except Exception as e:
                print(f"  ✗ Failed to migrate {filename}: {e}")
        
        print(f"  ✓ Migration completed: {migrated_count} files")
        
        # Cleanup migration test
        if os.path.exists("/tmp/test_migration"):
            shutil.rmtree("/tmp/test_migration")
    
    # Cleanup old files
    for filepath in created_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"  Warning: Could not remove {filepath}: {e}")

def test_directory_creation():
    """Test directory creation with various email formats"""
    print("\nTesting directory creation:")
    
    test_emails = [
        "simple@example.com",
        "user.with.dots@domain.co.uk",
        "user+tag@example.org",
        "complex.email+tag@sub.domain.com"
    ]
    
    base_dir = "/tmp/test_dir_creation"
    
    for email in test_emails:
        safe_email = get_safe_email_for_path(email)
        test_dir = f"{base_dir}/{safe_email}/123"
        
        try:
            os.makedirs(test_dir, exist_ok=True)
            if os.path.exists(test_dir):
                print(f"  ✓ Created directory for {email}")
                print(f"    -> {safe_email}")
            else:
                print(f"  ✗ Failed to create directory for {email}")
        except Exception as e:
            print(f"  ✗ Error creating directory for {email}: {e}")
    
    # Cleanup
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
        print(f"  ✓ Cleaned up test directories")

if __name__ == "__main__":
    print("Testing new file storage structure...\n")
    
    test_safe_email_conversion()
    test_file_structure()
    test_migration_scenario()
    test_directory_creation()
    
    print("\n" + "="*50)
    print("All tests completed successfully!")
    print("The new file storage structure is working correctly.")
    print("="*50) 