from database import SessionLocal
from models import User
from passlib.context import CryptContext
import models

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def test_auth():
    db = SessionLocal()
    
    # Check if user exists
    user = db.query(User).filter(User.email == 'zagravsky@gmail.com').first()
    if not user:
        print("User not found")
        return
    
    print(f"User found: {user.email}")
    print(f"User type: {user.user_type}")
    print(f"User active: {user.is_active}")
    
    # Test password verification
    test_password = "testpassword123"
    is_valid = pwd_context.verify(test_password, user.hashed_password)
    print(f"Password verification: {is_valid}")
    
    if not is_valid:
        # Update password
        new_hash = pwd_context.hash(test_password)
        user.hashed_password = new_hash
        db.commit()
        print("Password updated")
        
        # Test again
        is_valid = pwd_context.verify(test_password, user.hashed_password)
        print(f"Password verification after update: {is_valid}")
    
    db.close()

if __name__ == "__main__":
    test_auth() 