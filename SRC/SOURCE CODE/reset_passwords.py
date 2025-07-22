import sqlite3
from passlib.context import CryptContext
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Cấu hình bcrypt
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Mật khẩu mới mặc định
    new_password = "123"
    hashed_password = pwd_context.hash(new_password)

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect("check_results.db")
    cursor = conn.cursor()

    # Cập nhật mật khẩu cho tất cả tài khoản
    cursor.execute("UPDATE nguoi_dung SET mat_khau = ?", (hashed_password,))
    conn.commit()
    print(f"Đã cập nhật mật khẩu mới cho {cursor.rowcount} tài khoản. Mật khẩu mới là: {new_password}")

except Exception as e:
    logger.error(f"Lỗi khi cập nhật mật khẩu: {str(e)}")
    raise

finally:
    # Đóng kết nối
    if 'conn' in locals():
        conn.close()