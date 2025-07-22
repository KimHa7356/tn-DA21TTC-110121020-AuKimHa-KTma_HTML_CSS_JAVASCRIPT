from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_password = "admin"  # Giữ mật khẩu admin để nhất quán
hashed_password = pwd_context.hash(new_password)
print(hashed_password)