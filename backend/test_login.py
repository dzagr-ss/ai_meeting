from database import SessionLocal
from models import User
import crud
import schemas

def test_login():
    db = SessionLocal()
    
    # Test the authenticate_user function directly
    email = "zagravsky@gmail.com"
    password = "testpassword123"
    
    print(f"Testing login for: {email}")
    
    # Check if user exists
    user = crud.get_user_by_email(db, email)
    if user:
        print(f"User found: {user.email}, Type: {user.user_type}, Active: {user.is_active}")
    else:
        print("User not found")
        return
    
    # Test authentication
    auth_result = crud.authenticate_user(db, email, password)
    print(f"Authentication result: {auth_result}")
    
    if auth_result:
        print("Authentication successful!")
        # Test token creation
        token = crud.create_access_token(data={"sub": user.email, "user_type": user.user_type.value})
        print(f"Token created: {token[:50]}...")
    else:
        print("Authentication failed!")
    
    db.close()

if __name__ == "__main__":
    test_login() 