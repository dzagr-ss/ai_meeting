#!/usr/bin/env python3
"""
Railway Deployment Validation Script
Tests all critical components for Railway deployment
"""
import sys
import os
import importlib
import traceback
from pathlib import Path

# Test configuration
CRITICAL_MODULES = [
    'fastapi',
    'uvicorn', 
    'sqlalchemy',
    'pydantic',
    'openai',
    'google.generativeai',
    'torch',
    'numpy',
    'soundfile',
    'librosa',
    'scipy',
    'pydub',
    'redis',
    'magic',
    'slowapi'
]

OPTIONAL_MODULES = [
    'whisperx',
    'pyannote.audio', 
    'noisereduce',
    'transformers'
]

LOCAL_MODULES = [
    'config',
    'database', 
    'models',
    'schemas',
    'crud',
    'speaker_identification',
    'audio_processor',
    'email_service'
]

def test_critical_imports():
    """Test critical package imports"""
    print("🔍 Testing critical package imports...")
    failed = []
    
    for module in CRITICAL_MODULES:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed.append((module, str(e)))
    
    return len(failed) == 0, failed

def test_optional_imports():
    """Test optional package imports"""
    print("\n🔍 Testing optional package imports...")
    available = []
    unavailable = []
    
    for module in OPTIONAL_MODULES:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
            available.append(module)
        except ImportError as e:
            print(f"⚠️  {module}: {e}")
            unavailable.append(module)
    
    return available, unavailable

def test_local_imports():
    """Test local module imports"""
    print("\n🔍 Testing local module imports...")
    failed = []
    
    for module in LOCAL_MODULES:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed.append((module, str(e)))
            traceback.print_exc()
    
    return len(failed) == 0, failed

def test_environment_variables():
    """Test required environment variables"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY', 
        'OPENAI_API_KEY'
    ]
    
    optional_vars = [
        'GEMINI_API_KEY',
        'HUGGINGFACE_TOKEN',
        'SMTP_SERVER',
        'SMTP_USERNAME',
        'SMTP_PASSWORD'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} (set)")
        else:
            print(f"❌ {var} (missing)")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} (set)")
        else:
            print(f"⚠️  {var} (optional, not set)")
            missing_optional.append(var)
    
    return len(missing_required) == 0, missing_required, missing_optional

def test_directories():
    """Test required directories"""
    print("\n🔍 Testing required directories...")
    
    required_dirs = [
        '/app/storage',
        '/app/logs', 
        '/app/tmp',
        '/app/models'
    ]
    
    failed = []
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}")
        else:
            print(f"❌ {directory} (missing)")
            failed.append(directory)
    
    return len(failed) == 0, failed

def test_railway_specific():
    """Test Railway-specific configurations"""
    print("\n🔍 Testing Railway-specific configurations...")
    
    # Test PORT environment variable
    port = os.getenv('PORT', '8000')
    print(f"✅ PORT: {port}")
    
    # Test Railway volume mount
    storage_path = os.getenv('STORAGE_PATH', '/app/storage')
    print(f"✅ STORAGE_PATH: {storage_path}")
    
    # Test memory optimization settings
    tokenizers_parallel = os.getenv('TOKENIZERS_PARALLELISM', 'true')
    print(f"✅ TOKENIZERS_PARALLELISM: {tokenizers_parallel}")
    
    return True

def test_fastapi_import():
    """Test FastAPI app import"""
    print("\n🔍 Testing FastAPI app import...")
    
    try:
        from main import app
        print("✅ FastAPI app imported successfully")
        print(f"✅ App title: {app.title}")
        return True
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all deployment tests"""
    print("🚀 Railway Deployment Validation")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run all tests
    all_passed = True
    
    # Critical imports
    critical_ok, critical_failed = test_critical_imports()
    if not critical_ok:
        all_passed = False
        print(f"\n💥 {len(critical_failed)} critical imports failed!")
    
    # Optional imports
    available, unavailable = test_optional_imports()
    print(f"\n📊 Optional packages: {len(available)} available, {len(unavailable)} unavailable")
    
    # Local imports
    local_ok, local_failed = test_local_imports()
    if not local_ok:
        all_passed = False
        print(f"\n💥 {len(local_failed)} local imports failed!")
    
    # Environment variables
    env_ok, missing_req, missing_opt = test_environment_variables()
    if not env_ok:
        all_passed = False
        print(f"\n💥 {len(missing_req)} required environment variables missing!")
    
    # Directories
    dir_ok, missing_dirs = test_directories()
    if not dir_ok:
        print(f"\n⚠️  {len(missing_dirs)} directories missing (will be created)")
    
    # Railway-specific
    railway_ok = test_railway_specific()
    
    # FastAPI app
    app_ok = test_fastapi_import()
    if not app_ok:
        all_passed = False
    
    # Final verdict
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All critical tests passed! Ready for Railway deployment.")
        print(f"📊 Summary: {len(available)} optional ML packages available")
        if unavailable:
            print(f"⚠️  Unavailable packages: {', '.join(unavailable)}")
        sys.exit(0)
    else:
        print("💥 Some critical tests failed! Fix issues before deploying.")
        if critical_failed:
            print("❌ Critical package failures:")
            for pkg, error in critical_failed:
                print(f"   - {pkg}: {error}")
        if local_failed:
            print("❌ Local module failures:")
            for pkg, error in local_failed:
                print(f"   - {pkg}: {error}")
        if missing_req:
            print(f"❌ Missing required environment variables: {', '.join(missing_req)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 