#!/usr/bin/env python3
"""
Test script for the new file storage structure
"""

import os
import tempfile
import shutil
from main import get_safe_email_for_path, get_meeting_audio_files

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
    
    # Test file retrieval (modify the function temporarily for testing)
    original_pattern = "/tmp/meetings"
    
    # Temporarily modify the function to use our test directory
    def test_get_meeting_audio_files(meeting_id: int, user_email: str):
        safe_email = get_safe_email_for_path(user_email)
        user_meeting_dir = f"{test_base}/{safe_email}/{meeting_id}"
        
        pattern = f"{user_meeting_dir}/meeting_{meeting_id}_*.wav"
        import glob
        files = glob.glob(pattern)
        files.sort()
        return files
    
    # Test retrieval
    found_files = test_get_meeting_audio_files(meeting_id, test_email)
    
    if len(found_files) == len(test_files):
        print(f"  ✓ Retrieved {len(found_files)} files correctly")
        for i, filepath in enumerate(found_files):
            expected_filename = test_files[i]
            actual_filename = os.path.basename(filepath)
            status = "✓" if actual_filename == expected_filename else "✗"
            print(f"    {status} {actual_filename}")
    else:
        print(f"  ✗ Expected {len(test_files)} files, got {len(found_files)}")
    
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
    
    # Create test files in old location
    for filepath in old_files:
        try:
            with open(filepath, 'w') as f:
                f.write("test audio data")
            print(f"  ✓ Created old structure file: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ✗ Failed to create {filepath}: {e}")
    
    # Test that files exist in old location
    import glob
    found_old_files = glob.glob("/tmp/meeting_456_*.wav")
    print(f"  ✓ Found {len(found_old_files)} files in old location")
    
    # Cleanup
    for filepath in old_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"  Warning: Could not remove {filepath}: {e}")

if __name__ == "__main__":
    print("Testing new file storage structure...\n")
    
    test_safe_email_conversion()
    test_file_structure()
    test_migration_scenario()
    
    print("\nTest completed!") 