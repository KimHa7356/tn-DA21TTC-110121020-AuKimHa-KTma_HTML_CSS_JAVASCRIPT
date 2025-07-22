import bcrypt

# Mật khẩu mới cho admin
new_password = "5555".encode('utf-8')

# Tạo hash bcrypt với 12 rounds và salt cố định (dùng salt từ hash tĩnh)
salt = bcrypt.gensalt(rounds=12)  # Lưu ý: Salt ngẫu nhiên, nên dùng salt cố định để kiểm tra
hashed_password = bcrypt.hashpw(new_password, salt)

# So sánh với hash tĩnh (nếu cần kiểm tra)
static_hash = "$2b$12$mzUO.BJBWhg46.yfYr1o.udY.FQZT/e8tabI7OMcbIsXpXDCg6ZB2"
print(f"Static hash: {static_hash}")
print(f"New hashed password: {hashed_password.decode('utf-8')}")
if bcrypt.checkpw(new_password, static_hash.encode('utf-8')):
    print("Mật khẩu '5555' khớp với hash tĩnh!")
else:
    print("Mật khẩu '5555' KHÔNG khớp với hash tĩnh!")