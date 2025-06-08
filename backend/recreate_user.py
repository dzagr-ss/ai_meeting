from database import SessionLocal
from models import User
from passlib.context import CryptContext
import models

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

# Delete existing admin user and recreate
db.query(User).filter(User.email == 'zagravsky@gmail.com').delete()
db.commit()

# Create fresh admin user
hashed_password = pwd_context.hash('testpassword123')
admin_user = User(
    email='zagravsky@gmail.com',
    hashed_password=hashed_password,
    is_active=True,
    user_type=models.UserType.ADMIN
)
db.add(admin_user)
db.commit()
print('Fresh admin user created')

# Test authentication immediately
auth_result = pwd_context.verify('testpassword123', admin_user.hashed_password)
print(f'Password verification: {auth_result}')

db.close() 