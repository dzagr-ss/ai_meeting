import os
from database import SessionLocal
from models import User
import crud
from passlib.context import CryptContext

# Set environment variables like the backend does
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['SECRET_KEY'] = 'your-super-secret-jwt-key-min-32-characters-long-change-this-in-production'
os.environ['ENVIRONMENT'] = 'development'

def debug_auth():
    print("=== Debug Authentication ===")
    
    # Test database connection
    db = SessionLocal()
    
    # Check all users
    users = db.query(User).all()
    print(f"Total users in database: {len(users)}")
    
    for user in users:
        print(f"User: {user.email}")
        print(f"  Type: {user.user_type}")
        print(f"  Active: {user.is_active}")
        print(f"  Hashed password length: {len(user.hashed_password) if user.hashed_password else 0}")
    
    # Test authentication with the exact same method as the backend
    email = "zagravsky@gmail.com"
    password = "testpassword123"
    
    print(f"\n=== Testing authentication for {email} ===")
    
    # Step 1: Get user by email
    user = crud.get_user_by_email(db, email)
    if user:
        print(f"✓ User found: {user.email}")
    else:
        print("✗ User not found")
        db.close()
        return
    
    # Step 2: Test password verification
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    is_valid = pwd_context.verify(password, user.hashed_password)
    print(f"Password verification result: {is_valid}")
    
    # Step 3: Test full authentication
    auth_result = crud.authenticate_user(db, email, password)
    print(f"Full authentication result: {auth_result}")
    
    if auth_result:
        print("✓ Authentication successful!")
    else:
        print("✗ Authentication failed!")
    
    db.close()

if __name__ == "__main__":
    debug_auth() 