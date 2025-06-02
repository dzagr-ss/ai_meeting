#!/usr/bin/env python3
"""
Test script to verify libmagic installation and python-magic functionality
Run this script to debug libmagic issues in Railway deployment
"""

import sys
import os

def test_libmagic():
    print("=== LibMagic Test Script ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Test 1: Check if libmagic system library is available
    print("\n1. Testing system libmagic availability...")
    try:
        import ctypes.util
        libmagic_path = ctypes.util.find_library('magic')
        if libmagic_path:
            print(f"   ✓ System libmagic found at: {libmagic_path}")
        else:
            print("   ✗ System libmagic not found")
    except Exception as e:
        print(f"   ✗ Error checking system libmagic: {e}")
    
    # Test 2: Try importing python-magic
    print("\n2. Testing python-magic import...")
    try:
        import magic
        print("   ✓ python-magic imported successfully")
        
        # Test 3: Try using magic
        print("\n3. Testing magic functionality...")
        try:
            # Create a test file
            test_file = "/tmp/test.txt"
            with open(test_file, 'w') as f:
                f.write("Hello, world!")
            
            # Test magic.from_file
            file_type = magic.from_file(test_file, mime=True)
            print(f"   ✓ Magic detection works: {file_type}")
            
            # Clean up
            os.remove(test_file)
            
        except Exception as e:
            print(f"   ✗ Error using magic: {e}")
            print(f"   Error type: {type(e).__name__}")
            
    except ImportError as e:
        print(f"   ✗ Failed to import python-magic: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Test fallback
        print("\n4. Testing mimetypes fallback...")
        try:
            import mimetypes
            test_type, _ = mimetypes.guess_type("test.mp3")
            print(f"   ✓ Mimetypes fallback works: {test_type}")
        except Exception as e:
            print(f"   ✗ Mimetypes fallback failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_libmagic() 