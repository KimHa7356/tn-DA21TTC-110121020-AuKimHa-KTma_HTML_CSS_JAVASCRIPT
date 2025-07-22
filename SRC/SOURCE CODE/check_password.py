from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
is_valid = pwd_context.verify("123", "$2b$12$/rsitXH5vDVGOfEYvfeft.Un1pBuRd3Pi1.HJNWEtRgXqDHawvjS6")
print(is_valid)  # True nếu khớp, False nếu không