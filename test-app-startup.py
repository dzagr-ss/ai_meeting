#!/usr/bin/env python3
"""
Application Startup Test Script
Tests all critical imports and configurations before starting the main application
"""

import sys
import traceback
import os

def test_basic_imports():
    """Test basic Python imports"""
    print("=== Testing Basic Imports ===")
    
    basic_modules = [
        'json', 'os', 'sys', 'datetime', 'asyncio', 'logging',
        'pathlib', 'uuid', 'hashlib', 'secrets', 're'
    ]
    
    for module_name in basic_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    return True

def test_web_framework_imports():
    """Test web framework imports"""
    print("\n=== Testing Web Framework Imports ===")
    
    web_modules = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('starlette', 'Starlette'),
        ('pydantic', 'Pydantic'),
        ('itsdangerous', 'ItsDangerous')
    ]
    
    for module_name, display_name in web_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {display_name}: {version}")
        except Exception as e:
            print(f"❌ {display_name}: {e}")
            return False
    
    return True

def test_database_imports():
    """Test database imports"""
    print("\n=== Testing Database Imports ===")
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
        
        import psycopg2
        print(f"✅ Psycopg2: {psycopg2.__version__}")
        
        import alembic
        print(f"✅ Alembic: {alembic.__version__}")
        
        return True
    except Exception as e:
        print(f"❌ Database imports failed: {e}")
        return False

def test_application_imports():
    """Test application-specific imports"""
    print("\n=== Testing Application Imports ===")
    
    app_modules = [
        'config',
        'database', 
        'models',
        'schemas',
        'crud'
    ]
    
    for module_name in app_modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            print(f"   Error details: {traceback.format_exc()}")
            return False
    
    return True

def test_main_module():
    """Test main application module"""
    print("\n=== Testing Main Application Module ===")
    
    try:
        print("Importing main module...")
        import main
        print("✅ Main module imported")
        
        print("Testing FastAPI app access...")
        app = main.app
        print("✅ FastAPI app accessible")
        
        print(f"App title: {getattr(app, 'title', 'Unknown')}")
        print(f"App version: {getattr(app, 'version', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Main module test failed: {e}")
        print(f"   Full traceback:\n{traceback.format_exc()}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n=== Testing Environment Configuration ===")
    
    required_checks = [
        ('PORT', os.getenv('PORT', '8000')),
        ('ENVIRONMENT', os.getenv('ENVIRONMENT', 'development')),
        ('DATABASE_URL', os.getenv('DATABASE_URL', 'Not set')),
        ('SECRET_KEY', '***' if os.getenv('SECRET_KEY') else 'Not set')
    ]
    
    for var_name, var_value in required_checks:
        print(f"  {var_name}: {var_value}")
    
    return True

def test_file_system():
    """Test file system access"""
    print("\n=== Testing File System Access ===")
    
    try:
        # Test write access to /tmp
        test_file = '/tmp/railway_test.txt'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ /tmp directory writable")
        
        # Test current directory
        print(f"✅ Current directory: {os.getcwd()}")
        print(f"✅ Directory contents: {len(os.listdir('.'))} files")
        
        return True
    except Exception as e:
        print(f"❌ File system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Railway Application Startup Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_web_framework_imports,
        test_database_imports,
        test_file_system,
        test_environment,
        test_application_imports,
        test_main_module
    ]
    
    failed_tests = []
    
    for test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_func.__name__)
        except Exception as e:
            print(f"❌ {test_func.__name__} crashed: {e}")
            failed_tests.append(test_func.__name__)
    
    print("\n" + "=" * 50)
    if failed_tests:
        print(f"❌ {len(failed_tests)} test(s) failed:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print("\n💡 Check the error details above to identify the root cause.")
        return False
    else:
        print("✅ All tests passed! Application should start successfully.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 