
import jwt
from jwt import PyJWTError
import sys
import shutil
import os
import ast
import cssutils
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import json
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from jose import JWTError
from typing import Optional
from fastapi import Header

from starlette.requests import Request
from starlette.responses import Response

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from passlib.context import CryptContext
import sqlite3
from datetime import datetime, timedelta
import time
import logging
import random
import smtplib
from email.mime.text import MIMEText
from contextlib import asynccontextmanager

from backend.html_KT import check_html
from backend.css_KT import check_css
from backend.js_KT import check_js

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def is_admin(vai_tro: str) -> bool:
    return normalize_role(vai_tro) == "QuanTri"

def normalize_role(role: str) -> str:
    role_mapping = {
        "admin": "admin",
        "giang_vien": "giang_vien",
        "sinh_vien": "sinh_vien",
        "quan_tri": "admin",
        "giangvien": "giang_vien",
        "sinhvien": "sinh_vien",
        "QuanTri": "admin",
        "GiangVien": "giang_vien",
        "SinhVien": "sinh_vien",
        "teacher": "giang_vien",
        "student": "sinh_vien"
    }
    normalized = role_mapping.get(role.lower(), role.lower())
    if normalized not in ["admin", "giang_vien", "sinh_vien"]:
        raise ValueError(f"Vai trò không hợp lệ: {role}")
    return normalized


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("Khởi tạo cơ sở dữ liệu thành công")
    except Exception as e:
        logger.error(f"Không thể khởi tạo cơ sở dữ liệu: {str(e)}")
        raise
    yield
    logger.info("Ứng dụng đang tắt")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "http://localhost,http://127.0.0.1,http://localhost:3000,http://127.0.0.1:59900").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
images_dir = os.path.abspath("frontend/public/images")
os.makedirs(images_dir, exist_ok=True)
logger.info(f"Thư mục images đã được tạo hoặc đã tồn tại tại: {images_dir}")

app.mount("/public", StaticFiles(directory="frontend/public", html=True), name="public")
app.mount("/images", StaticFiles(directory=images_dir), name="images")

import secrets

SECRET_KEY = "your-secret-key"  # Thay bằng khóa bảo mật mạnh
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hàm xác thực mật khẩu
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dangnhap")


class RegisterRequest(BaseModel):
    ten_dang_nhap: str
    mat_khau: str
    ma_xac_nhan: str
    vai_tro: str
    email: str  # Thêm trường email

# Giả định verification_codes lưu mã xác nhận tạm thời
verification_codes: Dict[str, Dict[str, str]] = {}

# Pydantic model cho TaskResponse
class TaskResponse(BaseModel):
    ma_bai_tap: int
    ten_bai_tap: str
    han_nop: datetime
    trang_thai_bai_tap: str
    trang_thai_nop: str
    thoi_gian_nop: datetime | None
    lan_nop: int | None
    ma_lop: int
    ten_lop: str
# Model cho yêu cầu tạo tài khoản
class UserCreateRequest(BaseModel):
    email: str
    password: str


class StudentSubmissionStatus(BaseModel):
    ma_sinh_vien: int
    ten_dang_nhap: str
    trang_thai_nop: str
    thoi_gian_nop: Optional[str] = None
    lan_nop: Optional[int] = None

class UserCreate(BaseModel):
    ten_dang_nhap: str
    mat_khau: str
    email: str
    vai_tro: str
    ma_xac_nhan: str
    # Hàm băm mật khẩu
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

from pydantic import BaseModel

class UserStats(BaseModel):
    ten_dang_nhap: str
    vai_tro: str
    thoi_gian_tao: str
    check_code_count: int  # COUNT(*) luôn trả về int, nên không cần Optional
    submission_count: int  # COUNT(*) luôn trả về int, nên không cần Optional

class User(BaseModel):
    ten_dang_nhap: str
    vai_tro: str
    thoi_gian_tao: str = "Chưa xác định"

class UserInDB(User):
    ma_nguoi_dung: int
    mat_khau: str

class UserRegister(BaseModel):
    ten_dang_nhap: str
    mat_khau: str
    ma_xac_nhan: str
    vai_tro: str = "sinh_vien"

class EmailRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class CodeInput(BaseModel):
    html: str = ""
    css: str = ""
    js: str = ""
    languages: List[str]

class CodeCheck(BaseModel):
    codes: List[CodeInput]

class CodeCheckResponse(BaseModel):
    index: int
    status: str
    errors: List[dict]
    fixed_code: dict
    detected_languages: List[str]
    css_content: str = ""
    js_content: str = ""

class Exercise(BaseModel):
    tieu_de: str
    noi_dung: str
    han_nop: str
    thoi_gian_tao: Optional[str] = None
    mo_ta: Optional[str] = None
    ngon_ngu: str
    trang_thai: str

class ExerciseCreate(Exercise):
    ma_lop: Optional[List[int]] = None  # Làm ma_lop tùy chọn
    ma_giang_vien: int

class ExerciseInDB(Exercise):

    ma_bai_tap: int
    ma_giang_vien: int
    tap_tin_bai_tap: Optional[str] = None
    ten_lop: Optional[str] = None
    submitted: Optional[bool] = None
    ma_lop: Optional[List[int]] = None  # Làm ma_lop tùy chọn
    
class ExerciseInDB(BaseModel):
    ma_bai_tap: int
    ma_giang_vien: int
    tieu_de: str
    noi_dung: str  # Phải là str, không phải dict
    han_nop: Optional[str] = None  # Cho phép None hoặc chuỗi
    thoi_gian_tao: str
    mo_ta: Optional[str] = None
    ngon_ngu: str
    trang_thai: Optional[str] = None
    tap_tin_bai_tap: Optional[str] = None
    ten_lop: Optional[str] = None
    submitted: Optional[bool] = None
    ma_lop: Optional[List[int]] = None
class ErrorDetail(BaseModel):
    type: str
    message: str
    line: str | None = None  # Dòng lỗi, có thể là chuỗi hoặc None
    suggestion: str | None = None
    language: str | None = None
    see_more: str | None = None
    severity: str = "medium"  # Thêm trường severity, mặc định là "medium"

class CodeCheckInDB(BaseModel):
    ma_kiem_tra: int
    ma_sinh_vien: int
    ma_bai_tap: Optional[int]
    ma_nguon: str
    loi: List[ErrorDetail]
    thoi_gian_kiem_tra: str

class UserRequest(BaseModel):
    ten_dang_nhap: str

class UserUpdate(BaseModel):
    ten_dang_nhap: str
    ten_dang_nhap_moi: str

class Class(BaseModel):
    ten_lop: str
    ma_so_lop: str
    ngay_bat_dau: Optional[str] = None  # Định dạng YYYY-MM-DD
    ngay_ket_thuc: Optional[str] = None  # Định dạng YYYY-MM-DD


class Student(BaseModel):
    email: str
    password: str  # Thêm trường password
    ma_lop: str | None = None

class StudentList(BaseModel):
    students: List[Student]

class ClassInDB(Class):
    ma_lop: int
    ma_giang_vien: int
    thoi_gian_tao: str
    ngay_bat_dau: Optional[str] = None  # Thêm ngày bắt đầu
    ngay_ket_thuc: Optional[str] = None  # Thêm ngày kết thúc

class Teacher(BaseModel):
    email: str
    password: str

class TeacherList(BaseModel):
    teachers: List[Teacher]

class ExerciseUpdate(BaseModel):
    tieu_de: str
    noi_dung: str
    han_nop: str  # ISO 8601 datetime string
    mo_ta: Optional[str] = None
    ngon_ngu: str
    trang_thai: Optional[str] = "mo"  # Giá trị mặc định "mo"
    ma_lop: Optional[List[int]] = None  # Cho phép null hoặc danh sách rỗng

# Model kiem tra lop hoc co sinh vien khong
class Enrollment(BaseModel):
    ma_sinh_vien_lop_hoc: int
    ma_lop: int
    ma_sinh_vien: int
    ngay_dang_ky: str
    trang_thai: str


VERIFICATION_CODES = {}
VERIFICATION_CODE_EXPIRY = 300


# Định nghĩa đường dẫn tuyệt đối đến file check_results.db trong D:\WEBKL\backend
DB_PATH = os.path.abspath(os.path.join("D:\\WEBKL\\backend", "check_results.db"))

def init_db():
    with sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL;")
        db.execute("PRAGMA foreign_keys=ON;")
        logger.info("Bắt đầu khởi tạo cơ sở dữ liệu...")

        def execute_with_retry(query, params=()):
            for attempt in range(5):
                try:
                    cursor = db.cursor()
                    cursor.execute(query, params)
                    db.commit()
                    logger.debug(f"Thực thi truy vấn thành công: {query[:50]}...")
                    return
                except sqlite3.OperationalError as e:
                    logger.error(f"Lỗi truy vấn (lần {attempt + 1}): {str(e)} - Truy vấn: {query}")
                    if "database is locked" in str(e) and attempt < 4:
                        time.sleep(0.1)
                        continue
                    raise
        try:
            # Tạo bảng nguoi_dung (chỉ một lần, bao gồm email)

            logger.info("Bảng nguoi_dung đã được tạo hoặc đã tồn tại.")

            # Thêm tài khoản admin mặc định
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM nguoi_dung WHERE ten_dang_nhap = 'admin@gmail.com'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, vai_tro, email) VALUES (?, ?, ?, ?)",
                    ("admin@gmail.com", "$2b$12$/rsitXH5vDVGOfEYvfeft.Un1pBuRd3Pi1.HJNWEtRgXqDHawvjS6", "admin", "admin@gmail.com")
                )
                logger.info("Tạo tài khoản admin mặc định thành công")
            db.commit()


            # Các bảng khác (bai_nop, lop_hoc, bai_tap_lop_hoc, kiem_tra_ma, sinh_vien_lop_hoc)
            # Giữ nguyên vì chúng đã khớp với cấu trúc bạn cung cấp
            # (Lưu ý: Bảng lich_su_dang_nhap trong cấu trúc mới nhưng chưa có trong init_db, sẽ thêm sau)

        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo cơ sở dữ liệu: {str(e)}")
            raise

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: sqlite3.Connection, ten_dang_nhap: str):
    try:
        logger.debug(f"Truy vấn người dùng với ten_dang_nhap: {ten_dang_nhap}")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (ten_dang_nhap,))
        user = cursor.fetchone()
        logger.debug(f"Kết quả truy vấn: {user}")
        if user:
            return UserInDB(
                ten_dang_nhap=user["ten_dang_nhap"],
                mat_khau=user["mat_khau"],
                vai_tro=user["vai_tro"],
                thoi_gian_tao=user["thoi_gian_tao"]
            )
        return None
    except sqlite3.Error as e:
        logger.error(f"Lỗi khi lấy thông tin người dùng {ten_dang_nhap}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)  # Tăng từ 15 lên 60 phút
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Token không chứa username (sub)")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"Lỗi giải mã token: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Lỗi không xác định khi giải mã token: {str(e)}")
        raise HTTPException(status_code=500, detail="Lỗi server khi xác thực token")

    cursor = db.cursor()
    try:
        cursor = retry_on_locked(db, "SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (username,))
        user = cursor.fetchone()
        if user is None:
            logger.error(f"Không tìm thấy người dùng với username: {username}")
            raise credentials_exception
        user_data = UserInDB(
            ma_nguoi_dung=user["ma_nguoi_dung"],
            ten_dang_nhap=user["ten_dang_nhap"],
            mat_khau=user["mat_khau"],
            vai_tro=user["vai_tro"],
            thoi_gian_tao=user["thoi_gian_tao"]
        )
        logger.debug(f"Trả về user data: {user_data.dict()}")
        return user_data
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy thông tin người dùng: {str(e)}")
        raise HTTPException(status_code=500, detail="Lỗi cơ sở dữ liệu khi lấy thông tin người dùng")
def retry_on_locked(db, query, params, retries=5, delay=1.0):
    for attempt in range(retries):
        try:
            cursor = db.cursor()
            cursor.execute(query, params)
            db.commit()
            return cursor
        except sqlite3.OperationalError as e:
            logger.error(f"Lỗi truy vấn (lần {attempt + 1}): {str(e)} - Truy vấn: {query}")
            if "database is locked" in str(e) and attempt < retries - 1:
                time.sleep(delay)
                continue
            raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "kimha7356@gmail.com"
EMAIL_PASS = "mftm xmgi bvqj pvrt"

@app.post("/send_verification_code")
async def send_verification_code(request: EmailRequest):
    code = str(random.randint(100000, 999999))
    VERIFICATION_CODES[request.email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(seconds=VERIFICATION_CODE_EXPIRY)
    }

    msg = MIMEText(f"Mã xác nhận của bạn là: {code}\nMã có hiệu lực trong 5 phút.")
    msg["Subject"] = "Mã xác nhận đăng ký"
    msg["From"] = EMAIL_USER
    msg["To"] = request.email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi gửi email: {str(e)}")
    return {"message": "Mã xác nhận đã được gửi"}



@app.get("/check_token", include_in_schema=False)
@app.get("/check_token/", include_in_schema=False)
async def check_token(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug(f"Nhận token: {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Token không chứa username (sub)")
            raise credentials_exception
        logger.debug(f"Payload giải mã: {payload}")
    except JWTError as e:
        logger.error(f"Lỗi giải mã token: {str(e)}")
        raise credentials_exception
    
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung, ten_dang_nhap, vai_tro, anh_dai_dien, email FROM nguoi_dung WHERE ten_dang_nhap = ?", (username,))
    user = cursor.fetchone()
    
    if user is None:
        logger.error(f"Không tìm thấy người dùng với username: {username}")
        raise credentials_exception
    
    role_mapping = {"admin": "QuanTri", "giang_vien": "GiangVien", "sinh_vien": "SinhVien"}
    return {
        "ma_nguoi_dung": user["ma_nguoi_dung"],
        "ten_dang_nhap": user["ten_dang_nhap"],
        "vai_tro": role_mapping.get(user["vai_tro"], user["vai_tro"]),
        "anh_dai_dien": user["anh_dai_dien"],
        "email": user["email"]
    }
@app.post("/dangnhap", response_model=Token)
async def dang_nhap(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không đúng",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["ten_dang_nhap"]},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": user["ten_dang_nhap"]}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "ten_dang_nhap": user["ten_dang_nhap"],  # Thêm ten_dang_nhap
            "vai_tro": user["vai_tro"],  # Thêm vai_tro
            "email": user["email"]  # Thêm email
        }
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu trong quá trình đăng nhập: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except HTTPException as e:
        logger.warning(f"Xác thực thất bại: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Lỗi không xác định trong quá trình đăng nhập: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@app.get("/nvlophoc.html")
async def serve_nvlophoc():
    file_path = os.path.abspath("frontend/public/nvlophoc.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File nvlophoc.html not found")
    return FileResponse(file_path)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import sqlite3


async def check_token(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung, ten_dang_nhap, vai_tro, anh_dai_dien FROM nguoi_dung WHERE ten_dang_nhap = ?", (username,))
    user = cursor.fetchone()
    
    if user is None:
        raise credentials_exception
    
    # Chuyển đổi vai_tro thành định dạng chuẩn
    role_mapping = {
        "admin": "QuanTri",
        "giang_vien": "GiangVien",
        "sinh_vien": "SinhVien"
    }
    
    return {
        "ma_nguoi_dung": user[0],
        "ten_dang_nhap": user[1],
        "vai_tro": role_mapping.get(user[2], user[2]),
        "anh_dai_dien": user[3]
    }

# Token verification dependency
async def verify_token(authorization: str = Header(...)):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# Tasks endpoint
@app.get("/tasks/", response_model=List[TaskResponse])
async def get_tasks(ten_dang_nhap: str, token: dict = Depends(verify_token)):
    try:
        logger.debug(f"Fetching tasks for ten_dang_nhap: {ten_dang_nhap}")
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT 
            bt.ma_bai_tap,
            bt.tieu_de AS ten_bai_tap,
            bt.han_nop,
            bt.trang_thai AS trang_thai_bai_tap,
            COALESCE(bn.trang_thai, 'chua_nop') AS trang_thai_nop,
            bn.thoi_gian_nop,
            bn.lan_nop,
            lh.ma_lop,
            lh.ten_lop
        FROM nguoi_dung nd
        JOIN sinh_vien_lop_hoc svlh ON nd.ma_nguoi_dung = svlh.ma_sinh_vien
        JOIN lop_hoc lh ON svlh.ma_lop = lh.ma_lop
        JOIN bai_tap_lop_hoc btlh ON lh.ma_lop = btlh.ma_lop
        JOIN bai_tap bt ON btlh.ma_bai_tap = bt.ma_bai_tap
        LEFT JOIN bai_nop bn ON bt.ma_bai_tap = bn.ma_bai_tap 
            AND bn.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE nd.ten_dang_nhap = ? 
            AND svlh.trang_thai = 'hoat_dong'
            AND btlh.trang_thai = 'mo'
            AND bt.trang_thai = 'mo'
        ORDER BY bt.han_nop DESC
        """
        
        cursor.execute(query, (ten_dang_nhap,))
        tasks = cursor.fetchall()

        task_list = []
        for row in tasks:
            try:
                task_list.append(TaskResponse(
                    ma_bai_tap=row["ma_bai_tap"],
                    ten_bai_tap=row["ten_bai_tap"],
                    han_nop=datetime.fromisoformat(row["han_nop"]) if row["han_nop"] else None,
                    trang_thai_bai_tap=row["trang_thai_bai_tap"],
                    trang_thai_nop=row["trang_thai_nop"],
                    thoi_gian_nop=datetime.fromisoformat(row["thoi_gian_nop"]) if row["thoi_gian_nop"] else None,
                    lan_nop=row["lan_nop"],
                    ma_lop=row["ma_lop"],
                    ten_lop=row["ten_lop"]
                ))
            except ValueError as e:
                logger.error(f"Error parsing task data for ma_bai_tap {row['ma_bai_tap']}: {str(e)}")
                continue

        conn.close()
        logger.debug(f"Retrieved {len(task_list)} tasks for {ten_dang_nhap}")
        return task_list

    except sqlite3.Error as e:
        logger.error(f"Database error in get_tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
#lay bai tap
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def serve_devtools_json():
    file_path = "D:\\WEBKL\\frontend\\public\\.well-known\\appspecific\\com.chrome.devtools.json"
    logger.debug(f"Checking file at: {file_path}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.post("/add_students/")
async def add_students(
    student_list: StudentList,
    ma_lop: Optional[int] = None,
    current_user: dict = Depends(get_current_user),  # Sửa thành UserInDB
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    added_students = []
    failed_students = []

    if ma_lop:
        cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        class_item = cursor.fetchone()
        if not class_item:
            raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
    for student in student_list.students:
        try:
            # Kiểm tra email đã tồn tại
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM nguoi_dung WHERE email = ?)",
                (student.email,)
            )
            if cursor.fetchone()[0]:
                failed_students.append({
                    "email": student.email,
                    "reason": "Email đã tồn tại"
                })
                logger.info(f"Email {student.email} đã tồn tại, bỏ qua.")
                continue

            # Băm mật khẩu
            hashed_password = get_password_hash(student.password)
            ten_dang_nhap = student.email.split('@')[0]

            # Thêm sinh viên với trạng thái "hoat_dong"
            cursor.execute(
                """
                INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, email, vai_tro, trang_thai, thoi_gian_tao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ten_dang_nhap,
                    hashed_password,
                    student.email,
                    "sinh_vien",
                    "hoat_dong",  # Thay "cho_duyet" bằng "hoat_dong"
                    datetime.now().isoformat()
                )
            )
            logger.info(f"Thêm sinh viên {ten_dang_nhap} thành công.")

            # Lấy ma_nguoi_dung
            cursor.execute(
                "SELECT ma_nguoi_dung FROM nguoi_dung WHERE email = ?",
                (student.email,)
            )
            ma_sinh_vien = cursor.fetchone()[0]  # Lấy ma_nguoi_dung

            if ma_lop:
                cursor.execute(
                    """
                    SELECT EXISTS(SELECT 1 FROM sinh_vien_lop_hoc WHERE ma_lop = ? AND ma_sinh_vien = ?)
                    """,
                    (ma_lop, ma_sinh_vien)
                )
                if cursor.fetchone()[0]:
                    failed_students.append({
                        "email": student.email,
                        "reason": "Sinh viên đã có trong lớp này"
                    })
                else:
                    cursor.execute(
                        """
                        INSERT INTO sinh_vien_lop_hoc (ma_lop, ma_sinh_vien)
                        VALUES (?, ?)
                        """,
                        (ma_lop, ma_sinh_vien)
                    )
                    added_students.append({
                        "email": student.email,
                        "ma_lop": ma_lop
                    })
            else:
                added_students.append({"email": student.email})

        except sqlite3.IntegrityError as e:
            failed_students.append({
                "email": student.email,
                "reason": f"Lỗi dữ liệu: {str(e)}"
            })
            logger.error(f"Lỗi IntegrityError khi thêm {student.email}: {str(e)}")
        except Exception as e:
            failed_students.append({
                "email": student.email,
                "reason": f"Lỗi không xác định: {str(e)}"
            })
            logger.error(f"Lỗi không xác định khi thêm {student.email}: {str(e)}")

    db.commit()
    logger.info(f"Đã commit dữ liệu cho {len(student_list.students)} sinh viên.")

    return {
        "message": f"Đã xử lý {len(student_list.students)} sinh viên",
        "added_students": added_students,
        "failed_students": failed_students
    }

#xóa bài tập
@app.delete("/classes/{ma_lop}/exercises/{ma_bai_tap}")
async def remove_exercise_from_class(
    ma_lop: int,
    ma_bai_tap: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        # Kiểm tra xem lớp học có tồn tại không
        cursor = db.cursor()
        cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        class_record = cursor.fetchone()
        if not class_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lớp học không tồn tại"
            )

        # Kiểm tra xem bài tập có tồn tại không
        cursor.execute("SELECT * FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
        exercise_record = cursor.fetchone()
        if not exercise_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài tập không tồn tại"
            )

        # Kiểm tra xem bài tập có thuộc lớp học không
        cursor.execute(
            """
            SELECT * FROM bai_tap_lop_hoc
            WHERE ma_lop = ? AND ma_bai_tap = ?
            """,
            (ma_lop, ma_bai_tap)
        )
        relation_record = cursor.fetchone()
        if not relation_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài tập không thuộc lớp học này"
            )

        # Kiểm tra quyền của người dùng (Quản trị viên hoặc Giảng viên tạo bài tập)
        if current_user.vai_tro == "GiangVien":
            cursor.execute(
                "SELECT ma_giang_vien FROM bai_tap WHERE ma_bai_tap = ?",
                (ma_bai_tap,)
            )
            exercise_owner = cursor.fetchone()
            if exercise_owner and exercise_owner[0] != current_user.ma_nguoi_dung:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền xóa bài tập này"
                )
        elif current_user.vai_tro != "QuanTri":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xóa bài tập"
            )

        # Xóa mối quan hệ trong bảng bai_tap_lop_hoc
        cursor.execute(
            """
            DELETE FROM bai_tap_lop_hoc
            WHERE ma_lop = ? AND ma_bai_tap = ?
            """,
            (ma_lop, ma_bai_tap)
        )
        db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể xóa bài tập khỏi lớp học"
            )

        return {"message": "Gỡ bài tập thành công"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Lỗi không xác định khi xóa bài tập khỏi lớp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không xác định: {str(e)}"
        )

        # Xóa bài tập khỏi lớp học
        cursor.execute(
            "DELETE FROM bai_tap_lop_hoc WHERE ma_lop = ? AND ma_bai_tap = ?",
            (ma_lop, ma_bai_tap)
        )
        db.commit()

        logger.info(f"Đã xóa bài tập {ma_bai_tap} khỏi lớp {ma_lop} bởi người dùng {current_user.ten_dang_nhap}")
        return {"message": "Xóa bài tập khỏi lớp học thành công"}

    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi xóa bài tập khỏi lớp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi xóa bài tập khỏi lớp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
@app.post("/add_teachers/")
async def add_teachers(
    teacher_list: TeacherList,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    added_teachers = []
    failed_teachers = []

    # Loại bỏ kiểm tra quyền quản trị
    # if current_user.get("vai_tro") != "QuanTri":
    #     raise HTTPException(status_code=403, detail="Bạn không có quyền thêm giảng viên")

    for teacher in teacher_list.teachers:
        try:
            # Kiểm tra email đã tồn tại
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM nguoi_dung WHERE email = ?)",
                (teacher.email,)
            )
            if cursor.fetchone()[0]:
                failed_teachers.append({
                    "email": teacher.email,
                    "reason": "Email đã tồn tại"
                })
                logger.info(f"Email {teacher.email} đã tồn tại, bỏ qua.")
                continue

            # Băm mật khẩu
            hashed_password = get_password_hash(teacher.password)
            ten_dang_nhap = teacher.email.split('@')[0]

            # Thêm giảng viên với trạng thái "hoat_dong"
            cursor.execute(
                """
                INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, email, vai_tro, trang_thai, thoi_gian_tao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ten_dang_nhap,
                    hashed_password,
                    teacher.email,
                    "giang_vien",
                    "hoat_dong",
                    datetime.now().isoformat()
                )
            )
            logger.info(f"Thêm giảng viên {ten_dang_nhap} thành công.")

            added_teachers.append({"email": teacher.email})

        except sqlite3.IntegrityError as e:
            failed_teachers.append({
                "email": teacher.email,
                "reason": f"Lỗi dữ liệu: {str(e)}"
            })
            logger.error(f"Lỗi IntegrityError khi thêm {teacher.email}: {str(e)}")
        except Exception as e:
            failed_teachers.append({
                "email": teacher.email,
                "reason": f"Lỗi không xác định: {str(e)}"
            })
            logger.error(f"Lỗi không xác định khi thêm {teacher.email}: {str(e)}")

    db.commit()
    logger.info(f"Đã commit dữ liệu cho {len(teacher_list.teachers)} giảng viên.")

    # Tạo message chi tiết
    message_lines = [f"Đã xử lý {len(teacher_list.teachers)} giảng viên:"]
    if added_teachers:
        message_lines.append("Giảng viên được thêm thành công:")
        for teacher in added_teachers:
            message_lines.append(f"- {teacher['email']}")
    if failed_teachers:
        message_lines.append("Giảng viên không được thêm:")
        for teacher in failed_teachers:
            message_lines.append(f"- {teacher['email']}: {teacher['reason']}")
    if not added_teachers and not failed_teachers:
        message_lines.append("Không có giảng viên nào được thêm")

    return {
        "message": "\n".join(message_lines),
        "added_teachers": added_teachers,
        "failed_teachers": failed_teachers
    }



@app.get("/users/{ma_nguoi_dung}/", response_model=User)
async def get_user_by_id(ma_nguoi_dung: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Lấy thông tin người dùng (ten_dang_nhap) dựa trên ma_nguoi_dung.
    """
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT ten_dang_nhap, vai_tro, thoi_gian_tao FROM nguoi_dung WHERE ma_nguoi_dung = ?",
            (ma_nguoi_dung,)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        return User(
            ten_dang_nhap=user["ten_dang_nhap"],
            vai_tro=user["vai_tro"],
            thoi_gian_tao=user["thoi_gian_tao"]
        )
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy thông tin người dùng: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    

@app.get("/students/{email}/")
async def get_student_by_email(
    email: str,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Lấy thông tin sinh viên dựa trên email.
    Chỉ admin, giảng viên, hoặc chính chủ có quyền truy cập.
    """
    cursor = db.cursor()
    
    # Kiểm tra quyền truy cập
    vai_tro = current_user.get("vai_tro")
    if vai_tro not in ["QuanTri", "GiangVien", "SinhVien"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thông tin này")
    
    # Nếu là SinhVien, chỉ cho phép truy cập thông tin của chính mình
    if vai_tro == "SinhVien" and current_user.get("email") != email:
        raise HTTPException(status_code=403, detail="Bạn chỉ có thể xem thông tin của chính mình")

    # Truy vấn thông tin sinh viên dựa trên email
    cursor.execute(
        "SELECT ma_nguoi_dung, ten_dang_nhap, email, vai_tro, ma_lop FROM nguoi_dung WHERE email = ?",
        (email,)
    )
    student = cursor.fetchone()

    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")

    # Lấy thông tin lớp học (nếu có) từ bảng sinh_vien_lop_hoc
    cursor.execute(
        "SELECT ma_lop FROM sinh_vien_lop_hoc WHERE ma_sinh_vien = ?",
        (student["ma_nguoi_dung"],)
    )
    ma_lop_list = [row["ma_lop"] for row in cursor.fetchall()] or None

    return {
        "ma_nguoi_dung": student["ma_nguoi_dung"],
        "ten_dang_nhap": student["ten_dang_nhap"],
        "email": student["email"],
        "vai_tro": student["vai_tro"],
        "ma_lop": ma_lop_list  # Trả về danh sách mã lớp nếu có
    }


@app.post("/check_code/")
async def check_code(code_check: CodeCheck, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if len(code_check.codes) > 3:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ kiểm tra tối đa 3 mã cùng lúc")

    all_results = []
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()["ma_nguoi_dung"]

    for idx, code in enumerate(code_check.codes):
        errors = []
        fixed_codes = {"html": code.html, "css": code.css, "js": code.js}
        languages_to_check = code.languages
        detected_languages = []
        if code.html and ("<html>" in code.html.lower() or "<body>" in code.html.lower()):
            detected_languages.append("HTML")
        if code.css or "<style>" in code.html.lower():
            detected_languages.append("CSS")
        if code.js or "<script>" in code.html.lower():
            detected_languages.append("JavaScript")

        used_js_functions = set()
        if code.html:
            try:
                soup = BeautifulSoup(code.html, "html.parser")
                for tag in soup.find_all(True):
                    for attr_name, attr_value in tag.attrs.items():
                        if attr_name.startswith("on"):
                            matches = re.findall(r'\b(\w+)\s*\(\s*\)', attr_value)
                            used_js_functions.update(matches)
            except Exception as e:
                errors.append({
                    "type": "Lỗi phân tích",
                    "message": f"Lỗi khi phân tích HTML: {str(e)}",
                    "line": "N/A",
                    "suggestion": "Kiểm tra cú pháp HTML."
                })

        css_content = ""
        js_content = code.js

        if "HTML" in languages_to_check and code.html:
            html_result = check_html(code.html)
            errors.extend(html_result["errors"])
            fixed_codes["html"] = html_result.get("fixed_code", code.html)
            css_content = html_result.get("css_content", "")

            script_matches = re.findall(r"<script[^>]*>([\s\S]*?)<\/script>", code.html, re.IGNORECASE)
            if script_matches:
                for i, script_content in enumerate(script_matches):
                    js_content = (js_content + "\n" + script_content.strip()) if js_content else script_content.strip()
                    fixed_codes["html"] = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", fixed_codes["html"], count=1, flags=re.IGNORECASE)
                    errors.append({
                        "type": "Phát hiện mã JavaScript",
                        "message": f"Mã JavaScript được tìm thấy trong thẻ <script> thứ {i+1}.",
                        "line": code.html.count("\n", 0, code.html.find(script_content)) + 1,
                        "suggestion": "Tách mã JavaScript ra file riêng.",
                        "language": "JavaScript"
                    })
                fixed_codes["js"] = js_content

        if "CSS" in languages_to_check and (code.css or css_content):
            css_to_check = css_content if css_content else code.css
            css_result = check_css(css_to_check)
            errors.extend(css_result["errors"])
            fixed_codes["css"] = css_result.get("fixed_code", css_to_check)

        if "JavaScript" in languages_to_check and js_content:
            js_result = check_js(js_content, used_functions=used_js_functions)
            filtered_errors = [
                error for error in js_result["errors"]
                if not (error.get("rule") == "no-console" and "console.log" not in js_result["fixed_code"])
            ]
            errors.extend(filtered_errors)
            fixed_codes["js"] = js_result.get("fixed_code", js_content)
        status = "✅ Không có lỗi nào được phát hiện" if not errors else "❌ Mã có lỗi"

        for error in errors:
            if "line" in error and error["line"] is not None:
                error["line"] = str(error["line"])

        retry_on_locked(
            db,
            "INSERT INTO kiem_tra_ma (ma_sinh_vien, ma_nguon, loi, thoi_gian_kiem_tra) VALUES (?, ?, ?, ?)",
            (
                ma_nguoi_dung,
                json.dumps(fixed_codes),
                json.dumps(errors),
                datetime.now().isoformat()
            )
        )

        all_results.append(
            CodeCheckResponse(
                index=idx + 1,
                status=status,
                errors=errors,
                fixed_code=fixed_codes,
                detected_languages=detected_languages,
                css_content=css_content,
                js_content=js_content
            )
        )

    return all_results

@app.post("/refresh_token", response_model=Token)
async def refresh_token(refresh_token: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        ten_dang_nhap: str = payload.get("sub")
        if ten_dang_nhap is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = get_user(db, ten_dang_nhap)
    if user is None:
        raise credentials_exception
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.ten_dang_nhap}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.ten_dang_nhap}
    )
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "ten_dang_nhap": user.ten_dang_nhap,  # Thêm ten_dang_nhap
        "vai_tro": user.vai_tro  # Thêm vai_tro
    }

@app.get("/history/", response_model=List[CodeCheckInDB])
async def get_history(current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()["ma_nguoi_dung"]

    if current_user.vai_tro == "QuanTri":
        cursor.execute("SELECT * FROM kiem_tra_ma ORDER BY thoi_gian_kiem_tra DESC")
    else:
        cursor.execute(
            "SELECT * FROM kiem_tra_ma WHERE ma_sinh_vien = ? ORDER BY thoi_gian_kiem_tra DESC",
            (ma_nguoi_dung,)
        )
    checks = cursor.fetchall()
    history = []
    for check in checks:
        try:
            errors = json.loads(check["loi"]) if check["loi"] else []
            for error in errors:
                if "line" in error and error["line"] is not None:
                    error["line"] = str(error["line"])
            history.append({
                "ma_kiem_tra": check["ma_kiem_tra"],
                "ma_sinh_vien": check["ma_sinh_vien"],
                "ma_bai_tap": check["ma_bai_tap"],
                "ma_nguon": check["ma_nguon"],
                "loi": errors,
                "thoi_gian_kiem_tra": check["thoi_gian_kiem_tra"]
            })
        except json.JSONDecodeError:
            continue
    return history


#
@app.get("/exercise/content/{ma_bai_tap}")
async def get_exercise_content(ma_bai_tap: int, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_bai_tap, noi_dung FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    exercise = cursor.fetchone()
    if not exercise:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")

    try:
        # Giả định noi_dung là JSON hoặc chuỗi thô, cố gắng phân tích
        noi_dung = exercise["noi_dung"]
        if isinstance(noi_dung, str) and noi_dung.startswith("{"):
            content = json.loads(noi_dung)
        else:
            # Nếu không phải JSON, trả về chuỗi rỗng cho các trường
            content = {"html": "", "css": "", "js": ""}

        # Đảm bảo tất cả các trường đều có giá trị, mặc định rỗng nếu không tồn tại
        return {
            "ma_bai_tap": exercise["ma_bai_tap"],
            "html": content.get("html", ""),
            "css": content.get("css", ""),
            "js": content.get("js", "")
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Dữ liệu bài tập không hợp lệ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
#
@app.post("/exercises/", response_model=ExerciseInDB)
async def create_exercise(
    exercise: str = Form(...),
    exercise_file: UploadFile = File(None),
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        exercise_data = json.loads(exercise)
        
        cursor = db.cursor()
        cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
        ma_giang_vien = cursor.fetchone()["ma_nguoi_dung"]

        thoi_gian_tao = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO bai_tap (ma_giang_vien, tieu_de, noi_dung, han_nop, thoi_gian_tao, mo_ta, ngon_ngu, trang_thai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ma_giang_vien,
                exercise_data["tieu_de"],
                exercise_data["noi_dung"],
                exercise_data["han_nop"],
                thoi_gian_tao,
                exercise_data.get("mo_ta"),
                exercise_data["ngon_ngu"],
                "mo"
            )
        )
        ma_bai_tap = cursor.lastrowid

        file_path = None
        if exercise_file:
            upload_dir = "frontend/public/uploads/exercises"
            os.makedirs(upload_dir, exist_ok=True)
            file_extension = exercise_file.filename.split(".")[-1]
            file_name = f"exercise_{ma_bai_tap}.{file_extension}"
            file_path = os.path.join(upload_dir, file_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(exercise_file.file, buffer)
            cursor.execute(
                "UPDATE bai_tap SET tap_tin_bai_tap = ? WHERE ma_bai_tap = ?",
                (f"/uploads/exercises/{file_name}", ma_bai_tap)
            )

        # Chỉ xử lý ma_lop nếu nó được cung cấp
        ma_lop_list = exercise_data.get("ma_lop", None)
        if ma_lop_list:
            if not isinstance(ma_lop_list, list):
                raise ValueError("ma_lop phải là danh sách")
            for ma_lop in ma_lop_list:
                cursor.execute(
                    "INSERT INTO bai_tap_lop_hoc (ma_bai_tap, ma_lop) VALUES (?, ?)",
                    (ma_bai_tap, ma_lop)
                )

        db.commit()
        return ExerciseInDB(
            ma_bai_tap=ma_bai_tap,
            ma_giang_vien=ma_giang_vien,
            tieu_de=exercise_data["tieu_de"],
            noi_dung=exercise_data["noi_dung"],
            han_nop=exercise_data["han_nop"],
            thoi_gian_tao=thoi_gian_tao,
            mo_ta=exercise_data.get("mo_ta"),
            ngon_ngu=exercise_data["ngon_ngu"],
            trang_thai="mo",
            tap_tin_bai_tap=f"/uploads/exercises/{file_name}" if exercise_file else None,
            ten_lop=None,
            submitted=None,
            ma_lop=ma_lop_list
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Dữ liệu JSON không hợp lệ")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

@app.get("/exercise/{ma_bai_tap}")
async def get_exercise(ma_bai_tap: int, token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_bai_tap, noi_dung FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    exercise = cursor.fetchone()
    if not exercise:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    
    try:
        noi_dung = json.loads(exercise["noi_dung"]) if exercise["noi_dung"] else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Lỗi dữ liệu bài tập")
    
    return {
        "ma_bai_tap": exercise["ma_bai_tap"],
        "html": noi_dung.get("html", ""),
        "css": noi_dung.get("css", ""),
        "js": noi_dung.get("js", "")
    }
@app.get("/exercises/{ma_bai_tap}/", response_model=ExerciseInDB)
async def get_exercise_detail(
    ma_bai_tap: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT bt.*, GROUP_CONCAT(btlh.ma_lop) AS ma_lop
            FROM bai_tap bt
            LEFT JOIN bai_tap_lop_hoc btlh ON bt.ma_bai_tap = btlh.ma_bai_tap
            WHERE bt.ma_bai_tap = ?
            GROUP BY bt.ma_bai_tap
        """, (ma_bai_tap,))
        exercise = cursor.fetchone()

        if not exercise:
            raise HTTPException(status_code=404, detail="Bài tập không tồn tại")

        # Chỉ lấy các trường liên quan đến giao diện suaBT.html
        ma_lop_list = (
            [int(x) for x in exercise["ma_lop"].split(",") if x]
            if exercise["ma_lop"] and isinstance(exercise["ma_lop"], str)
            else None
        )

        return ExerciseInDB(
            ma_bai_tap=exercise["ma_bai_tap"],
            ma_giang_vien=exercise["ma_giang_vien"],
            tieu_de=exercise["tieu_de"],
            noi_dung=exercise["noi_dung"],
            han_nop=exercise["han_nop"],
            thoi_gian_tao=exercise["thoi_gian_tao"],
            mo_ta=exercise["mo_ta"],
            ngon_ngu=exercise["ngon_ngu"],
            trang_thai=exercise["trang_thai"],
            tap_tin_bai_tap=exercise["tap_tin_bai_tap"],
            ma_lop=ma_lop_list
        )
    except Exception as e:
        logger.error(f"Lỗi khi lấy bài tập {ma_bai_tap}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
@app.get("/exercises/", response_model=List[ExerciseInDB])
async def get_exercises(
    ma_giang_vien: Optional[int] = None,  # Thêm tham số tùy chọn
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()["ma_nguoi_dung"]
    vai_tro = normalize_role(current_user.vai_tro)

    try:
        exercises_data = []
        # Lọc bài tập theo ma_giang_vien nếu là giảng viên hoặc quản trị viên
        if vai_tro in ["GiangVien", "QuanTri"] and not ma_giang_vien:
            ma_giang_vien = ma_nguoi_dung
        elif vai_tro == "SinhVien":
            # Sinh viên không nên thấy tất cả bài tập, chỉ bài tập của lớp họ tham gia
            raise HTTPException(status_code=403, detail="Sinh viên không có quyền xem tất cả bài tập")

        query = """
            SELECT bt.*, GROUP_CONCAT(btlh.ma_lop) AS ma_lop
            FROM bai_tap bt
            LEFT JOIN bai_tap_lop_hoc btlh ON bt.ma_bai_tap = btlh.ma_bai_tap
        """
        params = []
        if ma_giang_vien:
            query += " WHERE bt.ma_giang_vien = ?"
            params.append(ma_giang_vien)
        query += " GROUP BY bt.ma_bai_tap ORDER BY bt.thoi_gian_tao DESC"

        cursor.execute(query, params)
        exercises = cursor.fetchall()

        for exercise in exercises:
            try:
                noi_dung = exercise["noi_dung"] if not exercise["noi_dung"] or exercise["noi_dung"].startswith("{") else json.loads(exercise["noi_dung"])
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi JSON trong noi_dung của bài tập {exercise['ma_bai_tap']}: {str(e)}")
                noi_dung = {}
            ma_lop = exercise["ma_lop"].split(",") if exercise["ma_lop"] else []
            exercise_data = {
                "ma_bai_tap": exercise["ma_bai_tap"],
                "ma_giang_vien": exercise["ma_giang_vien"],
                "tieu_de": exercise["tieu_de"],
                "noi_dung": noi_dung,
                "han_nop": exercise["han_nop"],
                "thoi_gian_tao": exercise["thoi_gian_tao"],
                "mo_ta": exercise["mo_ta"],
                "ngon_ngu": exercise["ngon_ngu"],
                "trang_thai": exercise["trang_thai"],
                "tap_tin_bai_tap": exercise["tap_tin_bai_tap"],
                "ten_lop": None,
                "submitted": None,
                "ma_lop": [int(x) for x in ma_lop] if ma_lop else None
            }
            exercises_data.append(ExerciseInDB(**exercise_data))

        return exercises_data
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy bài tập: {str(e)} - Query: {query}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        logger.error(f"Lỗi không xác định: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@app.get("/stats/", response_model=List[UserStats])
async def get_stats(current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    if current_user.vai_tro not in ["admin", "giang_vien"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem thống kê")
    
    cursor = db.cursor()
    try:
        query = """
            SELECT nd.ten_dang_nhap, nd.vai_tro, nd.thoi_gian_tao,
                   (SELECT COUNT(*) FROM kiem_tra_ma ktm WHERE ktm.ma_sinh_vien = nd.ma_nguoi_dung) as check_code_count,
                   (SELECT COUNT(*) FROM bai_nop bn WHERE bn.ma_sinh_vien = nd.ma_nguoi_dung) as submission_count
            FROM nguoi_dung nd
        """
        params = []
        if current_user.vai_tro == "giang_vien":
            query += " WHERE nd.vai_tro = 'sinh_vien'"
        
        logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        stats = cursor.fetchall()
        logger.debug(f"Retrieved {len(stats)} records from stats query")
        
        return [
            UserStats(
                ten_dang_nhap=stat["ten_dang_nhap"],
                vai_tro=stat["vai_tro"],
                thoi_gian_tao=stat["thoi_gian_tao"],
                check_code_count=int(stat["check_code_count"]),  # Ép kiểu để chắc chắn
                submission_count=int(stat["submission_count"])   # Ép kiểu để chắc chắn
            )
            for stat in stats
        ]
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy thống kê: {str(e)} - Query: {query}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

@app.get("/exercises/class/{ma_lop}", response_model=List[ExerciseInDB])
async def get_exercises_by_class(
    ma_lop: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()[0]  # Lấy mã giảng viên hiện tại
    vai_tro = normalize_role(current_user.vai_tro)

    try:
        # Kiểm tra lớp học tồn tại và quyền truy cập
        cursor.execute("SELECT ma_giang_vien FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        class_item = cursor.fetchone()
        if not class_item:
            raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
        if vai_tro == "GiangVien" and class_item["ma_giang_vien"] != ma_nguoi_dung:
            raise HTTPException(status_code=403, detail="Bạn không phải giảng viên của lớp này")

        # Lấy bài tập được gán cho lớp này với retry để tránh lock
        query = """
            SELECT bt.*, btlh.ma_lop, btlh.ngay_gan, btlh.trang_thai AS trang_thai_lop
            FROM bai_tap bt
            INNER JOIN bai_tap_lop_hoc btlh ON bt.ma_bai_tap = btlh.ma_bai_tap
            WHERE btlh.ma_lop = ? AND bt.trang_thai = 'mo' AND btlh.trang_thai = 'mo'
            ORDER BY btlh.ngay_gan DESC
        """
        for attempt in range(3):  # Thử lại tối đa 3 lần
            try:
                cursor.execute(query, (ma_lop,))
                exercises = cursor.fetchall()
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < 2:
                    time.sleep(0.1)
                    continue
                raise

        if not exercises:
            return []  # Trả về danh sách rỗng nếu không có bài tập

        exercises_data = []
        for exercise in exercises:
            try:
                noi_dung = exercise["noi_dung"] if not exercise["noi_dung"] or exercise["noi_dung"].startswith("{") else json.loads(exercise["noi_dung"])
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi JSON trong noi_dung của bài tập {exercise['ma_bai_tap']}: {str(e)}")
                noi_dung = {}
            ma_lop_list = [exercise["ma_lop"]] if exercise["ma_lop"] else []
            exercise_data = {
                "ma_bai_tap": exercise["ma_bai_tap"],
                "ma_giang_vien": exercise["ma_giang_vien"],
                "tieu_de": exercise["tieu_de"],
                "noi_dung": noi_dung,
                "han_nop": exercise["han_nop"],
                "thoi_gian_tao": exercise["thoi_gian_tao"],
                "mo_ta": exercise["mo_ta"],
                "ngon_ngu": exercise["ngon_ngu"],
                "trang_thai": exercise["trang_thai"],
                "tap_tin_bai_tap": exercise["tap_tin_bai_tap"],
                "ten_lop": None,
                "submitted": None,
                "ma_lop": ma_lop_list
            }
            exercises_data.append(ExerciseInDB(**exercise_data))

        return exercises_data
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy bài tập theo lớp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi không xác định: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@app.get("/users/check")
async def check_user(ten_dang_nhap: str, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute(
        "SELECT ma_nguoi_dung, vai_tro FROM nguoi_dung WHERE ten_dang_nhap = ?",
        (ten_dang_nhap,)
    )
    user = cursor.fetchone()

    if not user:
        return {"exists": False, "vai_tro": None}
    
    return {"exists": True, "vai_tro": user["vai_tro"]}

@app.get("/users/", response_model=List[User])
async def get_users(
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    role: Optional[str] = None,
    ten_dang_nhap: Optional[str] = None  # Thêm tham số ten_dang_nhap
):
    cursor = db.cursor()
    query = "SELECT ma_nguoi_dung, ten_dang_nhap, vai_tro, thoi_gian_tao FROM nguoi_dung"
    params = []

    if ten_dang_nhap:
        query += " WHERE ten_dang_nhap = ?"
        params.append(ten_dang_nhap)
    elif role:
        if current_user.vai_tro not in ["QuanTri", "GiangVien"]:
            raise HTTPException(status_code=403, detail="Bạn không có quyền lọc thông tin người dùng")
        query += " WHERE vai_tro = ?"
        params.append(role)
    elif current_user.vai_tro == "QuanTri":
        pass  # Lấy tất cả người dùng
    elif current_user.vai_tro == "GiangVien":
        query += " WHERE vai_tro = 'sinh_vien'"
    else:  # SinhVien
        query += " WHERE ten_dang_nhap = ?"
        params.append(current_user.ten_dang_nhap)

    try:
        cursor.execute(query, params)
        users = cursor.fetchall()
        if not users:
            return []  # Trả về mảng rỗng nếu không có dữ liệu
        return [
            User(
                ma_nguoi_dung=user["ma_nguoi_dung"],
                ten_dang_nhap=user["ten_dang_nhap"],
                vai_tro=user["vai_tro"],
                thoi_gian_tao=user["thoi_gian_tao"]
            ) for user in users
        ]
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy danh sách người dùng: {str(e)} - Query: {query}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
        
@app.get("/teachers/", response_model=List[User])
async def get_teachers(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = "SELECT ten_dang_nhap, vai_tro, thoi_gian_tao FROM nguoi_dung WHERE vai_tro = 'giang_vien' AND trang_thai = 'hoat_dong'"
    try:
        cursor.execute(query)
        teachers = cursor.fetchall()
        if not teachers:
            return []
        return [User(ten_dang_nhap=teacher["ten_dang_nhap"], vai_tro=teacher["vai_tro"], thoi_gian_tao=teacher["thoi_gian_tao"]) for teacher in teachers]
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy danh sách giảng viên: {str(e)} - Query: {query}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")


@app.get("/students/", response_model=List[User])
async def get_students(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = "SELECT ten_dang_nhap, vai_tro, thoi_gian_tao FROM nguoi_dung WHERE vai_tro = 'sinh_vien' AND trang_thai = 'hoat_dong'"
    try:
        cursor.execute(query)
        students = cursor.fetchall()
        if not students:
            return []
        return [User(ten_dang_nhap=student["ten_dang_nhap"], vai_tro=student["vai_tro"], thoi_gian_tao=student["thoi_gian_tao"]) for student in students]
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy danh sách sinh viên: {str(e)} - Query: {query}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    
@app.put("/exercises/{ma_bai_tap}/", response_model=ExerciseInDB)
async def update_exercise(
    ma_bai_tap: int,
    exercise: ExerciseUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    existing_exercise = cursor.fetchone()
    if not existing_exercise:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")

    try:
        retry_on_locked(
            db,
            """
            UPDATE bai_tap SET 
                tieu_de = ?, 
                noi_dung = ?, 
                han_nop = ?, 
                mo_ta = ?, 
                ngon_ngu = ?, 
                trang_thai = ?
            WHERE ma_bai_tap = ?
            """,
            (
                exercise.tieu_de,
                exercise.noi_dung,
                exercise.han_nop,
                exercise.mo_ta,
                exercise.ngon_ngu,
                exercise.trang_thai,
                ma_bai_tap
            )
        )

        # Xử lý ma_lop
        cursor.execute("DELETE FROM bai_tap_lop_hoc WHERE ma_bai_tap = ?", (ma_bai_tap,))
        if exercise.ma_lop:
            for ma_lop in exercise.ma_lop:
                cursor.execute(
                    "INSERT INTO bai_tap_lop_hoc (ma_bai_tap, ma_lop) VALUES (?, ?)",
                    (ma_bai_tap, ma_lop)
                )

        db.commit()

        return ExerciseInDB(
            ma_bai_tap=ma_bai_tap,
            ma_giang_vien=existing_exercise["ma_giang_vien"],
            tieu_de=exercise.tieu_de,
            noi_dung=exercise.noi_dung,
            han_nop=exercise.han_nop,
            thoi_gian_tao=existing_exercise["thoi_gian_tao"],
            mo_ta=exercise.mo_ta,
            ngon_ngu=exercise.ngon_ngu,
            trang_thai=exercise.trang_thai,
            tap_tin_bai_tap=existing_exercise["tap_tin_bai_tap"],
            ma_lop=exercise.ma_lop
        )
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

@app.delete("/exercises/{ma_bai_tap}/")
async def delete_exercise(
    ma_bai_tap: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_giang_vien = cursor.fetchone()["ma_nguoi_dung"]

    cursor.execute("SELECT * FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    exercise = cursor.fetchone()
    if not exercise:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")

    # Bỏ kiểm tra quyền: is_admin(vai_tro) và exercise["ma_giang_vien"] != ma_giang_vien
    
    retry_on_locked(
        db,
        "DELETE FROM bai_tap WHERE ma_bai_tap = ?",
        (ma_bai_tap,)
    )
    return {"message": "Xóa bài tập thành công"}

#them bai tap vao bai_tap_lop_hoc
@app.post("/classes/{class_id}/assign_exercise/")
async def assign_exercise_to_class(
    class_id: int,
    task_id: int = Form(...),  # ID của bài tập cần gán
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_giang_vien = cursor.fetchone()["ma_nguoi_dung"]

    # Kiểm tra lớp học tồn tại và quyền của giảng viên
    cursor.execute("SELECT ma_giang_vien FROM lop_hoc WHERE ma_lop = ?", (class_id,))
    class_item = cursor.fetchone()
    if not class_item or class_item["ma_giang_vien"] != ma_giang_vien:
        raise HTTPException(status_code=403, detail="Bạn không có quyền gán bài tập cho lớp này")

    # Kiểm tra bài tập tồn tại
    cursor.execute("SELECT ma_bai_tap FROM bai_tap WHERE ma_bai_tap = ? AND ma_giang_vien = ?", (task_id, ma_giang_vien))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại hoặc không thuộc về bạn")

    # Kiểm tra xem bài tập đã được gán cho lớp chưa
    cursor.execute("SELECT EXISTS(SELECT 1 FROM bai_tap_lop_hoc WHERE ma_bai_tap = ? AND ma_lop = ?)", (task_id, class_id))
    if cursor.fetchone()[0]:
        raise HTTPException(status_code=400, detail="Bài tập đã được gán cho lớp này")

    # Gán bài tập vào bảng bai_tap_lop_hoc
    try:
        retry_on_locked(
            db,
            "INSERT INTO bai_tap_lop_hoc (ma_bai_tap, ma_lop, ngay_gan, trang_thai) VALUES (?, ?, CURRENT_TIMESTAMP, 'mo')",
            (task_id, class_id)
        )
        db.commit()
        logger.info(f"Gán bài tập {task_id} cho lớp {class_id} thành công")
        return {"message": "Gán bài tập thành công", "ma_bai_tap": task_id, "ma_lop": class_id}
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Lỗi cơ sở dữ liệu khi gán bài tập: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    
@app.get("/thongtin/giangvien")
async def serve_thongtin_giangvien():
    return FileResponse("frontend/public/ttGV.html")

@app.get("/thongtin/sinhvien")
async def serve_thongtin_sinhvien():
    return FileResponse("frontend/public/ttSV.html")

@app.get("/lop/{ma_lop}")
async def serve_lop(ma_lop: int):
    return FileResponse("frontend/public/lop.html")

@app.get("/chinhsuathongtin")
async def serve_chinhsuathongtin():
    return FileResponse("frontend/public/chinhsuathongtin.html")

@app.get("/thongke")
async def serve_thongke():
    return FileResponse("frontend/public/thongke.html")

@app.get("/timkiemlophoc")
async def serve_timkiemlophoc():
    return FileResponse("frontend/public/timkiemlophoc.html")

@app.get("/lop/{class_id}")
async def serve_lop(class_id: int):
    return FileResponse("frontend/public/lop.html")

@app.get("/danhsachbaitap")
async def serve_danhsachbaitap():
    return FileResponse("frontend/public/dsBT.html")

@app.get("/danhsachlop")
async def serve_danhsachlop():
    return FileResponse("frontend/public/danhsachlop.html")

@app.get("/suaBT")
async def serve_suaBT():
    file_path = os.path.abspath("frontend/public/suaBT.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File suaBT.html not found")
    return FileResponse(file_path)

@app.get("/lophoc.html")
async def serve_lophoc():
    return FileResponse("frontend/public/lophoc.html")
@app.get("/taolophoc")
async def serve_taolophoc():
    return FileResponse("frontend/public/taolophoc.html")

@app.put("/users/")
async def update_user(
    file: UploadFile = File(None),
    ma_nguoi_dung: str = Form(None),
    ten_dang_nhap: str = Form(None),
    email: str = Form(None),
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    user_id = current_user.ma_nguoi_dung  # Sử dụng thuộc tính trực tiếp
    if not user_id:
        raise HTTPException(status_code=401, detail="Người dùng không hợp lệ")

    # Kiểm tra nếu ma_nguoi_dung từ Form khớp với current_user
    if ma_nguoi_dung and int(ma_nguoi_dung) != user_id:
        raise HTTPException(status_code=403, detail="Không có quyền cập nhật thông tin người dùng khác")

    # Cập nhật thông tin người dùng
    update_data = {}
    if ten_dang_nhap:
        update_data["ten_dang_nhap"] = ten_dang_nhap
    if email:
        cursor.execute("SELECT EXISTS(SELECT 1 FROM nguoi_dung WHERE email = ? AND ma_nguoi_dung != ?)", (email, user_id))
        if cursor.fetchone()[0]:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        update_data["email"] = email

    if file:
        upload_dir = "frontend/public/uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"avatar_{user_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        update_data["anh_dai_dien"] = f"/uploads/avatars/avatar_{user_id}_{file.filename}"

    if not update_data:
        return {"message": "Không có thay đổi để lưu", "anh_dai_dien": current_user.anh_dai_dien if hasattr(current_user, "anh_dai_dien") else None}

    # Cập nhật vào cơ sở dữ liệu
    set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
    query = f"UPDATE nguoi_dung SET {set_clause} WHERE ma_nguoi_dung = ?"
    params = list(update_data.values()) + [user_id]

    try:
        cursor.execute(query, params)
        db.commit()
        return {
            "message": "Cập nhật thông tin thành công",
            "anh_dai_dien": update_data.get("anh_dai_dien", current_user.anh_dai_dien if hasattr(current_user, "anh_dai_dien") else None)
        }
    except sqlite3.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")


# Thêm ngay sau khi định nghĩa app và middleware CORS
uploads_dir = os.path.abspath("frontend/public/uploads")
os.makedirs(uploads_dir, exist_ok=True)
logger.info(f"Thư mục uploads đã được tạo hoặc đã tồn tại tại: {uploads_dir}")

app.mount("/uploads", StaticFiles(directory="frontend/public/uploads"), name="uploads")

# Giữ nguyên các mount hiện tại
app.mount("/public", StaticFiles(directory="frontend/public", html=True), name="public")
app.mount("/images", StaticFiles(directory=images_dir), name="images")



#đoạn này hiển thị danh sách lớp của giảng viên đóa tạo
@app.get("/classes/")
async def get_classes(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM lop_hoc")
    classes = cursor.fetchall()
    return [dict(row) for row in classes]

@app.post("/classes/", response_model=ClassInDB)
async def create_class(class_data: Class, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_giang_vien = cursor.fetchone()["ma_nguoi_dung"]

    thoi_gian_tao = datetime.now().isoformat()
    retry_on_locked(
        db,
        "INSERT INTO lop_hoc (ma_giang_vien, ten_lop, ma_so_lop, thoi_gian_tao, ngay_bat_dau, ngay_ket_thuc) VALUES (?, ?, ?, ?, ?, ?)",
        (
            ma_giang_vien,
            class_data.ten_lop,
            class_data.ma_so_lop,
            thoi_gian_tao,
            class_data.ngay_bat_dau,  # Thêm trường ngày bắt đầu
            class_data.ngay_ket_thuc   # Thêm trường ngày kết thúc
        )
    )
    
    cursor.execute("SELECT last_insert_rowid()")
    ma_lop = cursor.fetchone()[0]
    
    db.commit()

    return ClassInDB(
        ma_lop=ma_lop,
        ma_giang_vien=ma_giang_vien,
        ten_lop=class_data.ten_lop,
        ma_so_lop=class_data.ma_so_lop,
        thoi_gian_tao=thoi_gian_tao,
        ngay_bat_dau=class_data.ngay_bat_dau,  # Thêm vào response
        ngay_ket_thuc=class_data.ngay_ket_thuc   # Thêm vào response
    )

# Kiểm tra xem sinh viên có tham gia lớp học không
@app.get("/enrollments/{ma_lop}/{ma_nguoi_dung}", response_model=Enrollment)
async def check_enrollment(ma_lop: int, ma_nguoi_dung: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM sinh_vien_lop_hoc 
            WHERE ma_lop = ? AND ma_sinh_vien = ?
            """,
            (ma_lop, ma_nguoi_dung)
        )
        enrollment = cursor.fetchone()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Sinh viên chưa tham gia lớp học này")
        return Enrollment(**enrollment)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/classes/{ma_lop}")
async def get_class_detail(ma_lop: int, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT lh.*, nd.ten_dang_nhap AS teacher_name,
            (SELECT COUNT(*) FROM sinh_vien_lop_hoc svlh WHERE svlh.ma_lop = lh.ma_lop) AS student_count
        FROM lop_hoc lh
        LEFT JOIN nguoi_dung nd ON lh.ma_giang_vien = nd.ma_nguoi_dung
        WHERE lh.ma_lop = ?
    """, (ma_lop,))
    class_data = cursor.fetchone()
    if not class_data:
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
    
    return {
        "ma_lop": class_data["ma_lop"],
        "ma_giang_vien": class_data["ma_giang_vien"],
        "ten_lop": class_data["ten_lop"],
        "ma_so_lop": class_data["ma_so_lop"],
        "thoi_gian_tao": class_data["thoi_gian_tao"],
        "teacher_name": class_data["teacher_name"],
        "student_count": class_data["student_count"],
        "ten_dang_nhap": current_user["ten_dang_nhap"]  # Thêm ten_dang_nhap của người dùng hiện tại
    }

@app.get("/classes/", response_model=list[dict])
async def get_classes(current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    ma_nguoi_dung = current_user.ma_nguoi_dung
    vai_tro = normalize_role(current_user.vai_tro)

    if vai_tro == "admin":
        cursor.execute("SELECT * FROM lop_hoc")
    elif vai_tro == "giang_vien":
        cursor.execute("SELECT * FROM lop_hoc WHERE ma_giang_vien = ?", (ma_nguoi_dung,))
    elif vai_tro == "sinh_vien":
        cursor.execute("""
            SELECT lh.*
            FROM lop_hoc lh
            INNER JOIN sinh_vien_lop_hoc svlh ON lh.ma_lop = svlh.ma_lop
            WHERE svlh.ma_sinh_vien = ?
        """, (ma_nguoi_dung,))
    else:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")

    classes = cursor.fetchall()
    result = [{
        "ma_lop": class_item["ma_lop"],
        "ten_lop": class_item["ten_lop"],
        "ma_so_lop": class_item["ma_so_lop"],
        "ma_giang_vien": class_item["ma_giang_vien"],
        "thoi_gian_tao": class_item["thoi_gian_tao"],
        "trang_thai": class_item["trang_thai"],
        "ngay_bat_dau": class_item["ngay_bat_dau"],
        "ngay_ket_thuc": class_item["ngay_ket_thuc"],
        "mo_ta": class_item["mo_ta"]
    } for class_item in classes]
    return result


@app.get("/classes/{ma_lop}/student_count", response_model=int)
async def get_student_count(ma_lop: int, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS student_count
        FROM sinh_vien_lop_hoc svlh
        LEFT JOIN nguoi_dung nd ON svlh.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE svlh.ma_lop = ? AND svlh.trang_thai = 'hoat_dong' AND nd.vai_tro = 'sinh_vien'
    """, (ma_lop,))
    student_count = cursor.fetchone()["student_count"]
    return student_count

@app.post("/classes/{ma_lop}/students/", response_model=dict)
async def add_student_to_class(ma_lop: int, student_data: dict, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()[0]
    vai_tro = normalize_role(current_user.vai_tro)

    if vai_tro not in ["admin", "giang_vien"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thêm sinh viên")

    cursor.execute("SELECT ma_giang_vien FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
    giang_vien = cursor.fetchone()
    if not giang_vien or (vai_tro == "giang_vien" and giang_vien[0] != ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Bạn không phải giảng viên của lớp này")

    student_ten_dang_nhap = student_data.get("student_ten_dang_nhap")
    if not student_ten_dang_nhap:
        raise HTTPException(status_code=400, detail="Tên đăng nhập sinh viên là bắt buộc")

    cursor.execute("SELECT ma_nguoi_dung, vai_tro FROM nguoi_dung WHERE ten_dang_nhap = ?", (student_ten_dang_nhap,))
    student = cursor.fetchone()
    if not student or student["vai_tro"] != "sinh_vien":
        raise HTTPException(status_code=400, detail="Sinh viên không tồn tại hoặc không phải vai trò sinh viên")

    ma_sinh_vien = student["ma_nguoi_dung"]
    try:
        cursor.execute("""
            INSERT INTO sinh_vien_lop_hoc (ma_lop, ma_sinh_vien, ngay_dang_ky, trang_thai)
            VALUES (?, ?, CURRENT_TIMESTAMP, 'hoat_dong')
            ON CONFLICT(ma_lop, ma_sinh_vien) DO UPDATE SET trang_thai = 'hoat_dong'
        """, (ma_lop, ma_sinh_vien))
        db.commit()
        return {"message": f"Thêm sinh viên {student_ten_dang_nhap} thành công", "ma_lop": ma_lop}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Sinh viên đã tồn tại trong lớp này")
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")


#hàm lấy tên giảng viên 
@app.get("/get_teacher_name/{ma_giang_vien}", response_model=str)
async def get_teacher_name(ma_giang_vien: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
        # Kiểm tra xem ma_giang_vien có hợp lệ không
        if not isinstance(ma_giang_vien, int) or ma_giang_vien <= 0:
            raise HTTPException(status_code=422, detail="Mã giảng viên không hợp lệ")
        
        cursor.execute(
            "SELECT ten_dang_nhap FROM nguoi_dung WHERE ma_nguoi_dung = ? AND vai_tro = 'giang_vien'",
            (ma_giang_vien,)
        )
        teacher = cursor.fetchone()
        if not teacher:
            raise HTTPException(status_code=404, detail="Giảng viên không tồn tại")
        return teacher["ten_dang_nhap"]
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy tên giảng viên: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    finally:
        cursor.close()
#hàm lấy tên giảng viên 
@app.put("/classes/{ma_lop}/", response_model=ClassInDB)
async def update_class(ma_lop: int, class_data: Class, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_giang_vien = cursor.fetchone()["ma_nguoi_dung"]

    cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
    class_item = cursor.fetchone()
    if not class_item:
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
    
    try:
        retry_on_locked(
            db,
            "UPDATE lop_hoc SET ten_lop = ?, ma_so_lop = ? WHERE ma_lop = ?",
            (class_data.ten_lop, class_data.ma_so_lop, ma_lop)
        )
        db.commit()  # Đảm bảo commit sau khi cập nhật
        return ClassInDB(
            ma_lop=ma_lop,
            ma_giang_vien=class_item["ma_giang_vien"],
            ten_lop=class_data.ten_lop,
            ma_so_lop=class_data.ma_so_lop,
            thoi_gian_tao=class_item["thoi_gian_tao"]
        )
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Lỗi cơ sở dữ liệu khi cập nhật lớp học: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    

    
@app.delete("/classes/{ma_lop}/")
async def delete_class(ma_lop: int, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Lấy mã người dùng hiện tại
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung_row = cursor.fetchone()
    if not ma_nguoi_dung_row:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    ma_nguoi_dung = ma_nguoi_dung_row["ma_nguoi_dung"]

    try:
        # Chuẩn hóa vai trò
        vai_tro = normalize_role(current_user.vai_tro)

        # Kiểm tra lớp học tồn tại
        cursor.execute("SELECT ma_giang_vien FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        class_item = cursor.fetchone()
        if not class_item:
            raise HTTPException(status_code=404, detail="Lớp học không tồn tại")

        # Kiểm tra quyền xóa
        if vai_tro != "admin" and class_item["ma_giang_vien"] != ma_nguoi_dung:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa lớp học này")

        # Kiểm tra số lượng sinh viên
        cursor.execute("SELECT COUNT(*) as count FROM sinh_vien_lop_hoc WHERE ma_lop = ?", (ma_lop,))
        student_count = cursor.fetchone()["count"]
        if student_count > 0:
            raise HTTPException(status_code=400, detail="Không thể xóa lớp học vì đã có sinh viên tham gia")

        # Xóa các bài tập liên quan
        cursor.execute("SELECT COUNT(*) as count FROM bai_tap_lop_hoc WHERE ma_lop = ?", (ma_lop,))
        assignment_count = cursor.fetchone()["count"]
        if assignment_count > 0:
            retry_on_locked(db, "DELETE FROM bai_tap_lop_hoc WHERE ma_lop = ?", (ma_lop,))
            logger.info(f"Đã xóa {assignment_count} bài tập liên quan đến lớp học {ma_lop}")

        # Xóa lớp học
        retry_on_locked(db, "DELETE FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        db.commit()

        logger.info(f"Xóa lớp học {ma_lop} thành công")
        return {"message": "Xóa lớp học thành công"}

    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Lỗi cơ sở dữ liệu khi xóa lớp học {ma_lop}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi không xác định khi xóa lớp học {ma_lop}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
@app.get("/classes/{ma_lop}/", response_model=dict)
async def get_class_details(ma_lop: int, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung_row = cursor.fetchone()
    if not ma_nguoi_dung_row:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    ma_nguoi_dung = ma_nguoi_dung_row["ma_nguoi_dung"]

    try:
        vai_tro = normalize_role(current_user.vai_tro)

        if vai_tro == "admin":
            cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
        elif vai_tro == "giang_vien":
            cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ? AND ma_giang_vien = ?", (ma_lop, ma_nguoi_dung))
        elif vai_tro == "sinh_vien":
            cursor.execute("""
                SELECT lh.*
                FROM lop_hoc lh
                INNER JOIN sinh_vien_lop_hoc svlh ON lh.ma_lop = svlh.ma_lop
                WHERE lh.ma_lop = ? AND svlh.ma_sinh_vien = ?
            """, (ma_lop, ma_nguoi_dung))
        else:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem chi tiết lớp học")

        class_item = cursor.fetchone()
        if not class_item:
            raise HTTPException(status_code=404, detail="Lớp học không tồn tại hoặc bạn không có quyền truy cập")

        # Lấy thông tin người tạo (ten_dang_nhap)
        cursor.execute("SELECT ten_dang_nhap FROM nguoi_dung WHERE ma_nguoi_dung = ?", (class_item["ma_giang_vien"],))
        teacher = cursor.fetchone()
        teacher_name = teacher["ten_dang_nhap"] if teacher else "Không xác định"

        # Lấy số lượng sinh viên
        cursor.execute("""
            SELECT COUNT(svlh.ma_sinh_vien) AS student_count
            FROM sinh_vien_lop_hoc svlh
            LEFT JOIN nguoi_dung nd ON svlh.ma_sinh_vien = nd.ma_nguoi_dung
            WHERE svlh.ma_lop = ? AND svlh.trang_thai = 'hoat_dong' AND nd.vai_tro = 'sinh_vien'
        """, (ma_lop,))
        student_count = cursor.fetchone()["student_count"]

        # Lấy danh sách sinh viên
        students = []
        cursor.execute("SELECT ma_sinh_vien FROM sinh_vien_lop_hoc WHERE ma_lop = ? AND trang_thai = 'hoat_dong'", (ma_lop,))
        student_rows = cursor.fetchall()
        for row in student_rows:
            cursor.execute("SELECT ten_dang_nhap FROM nguoi_dung WHERE ma_nguoi_dung = ? AND vai_tro = 'sinh_vien'", (row["ma_sinh_vien"],))
            student = cursor.fetchone()
            if student:
                students.append(student["ten_dang_nhap"])

        ngay_tao = class_item["thoi_gian_tao"].split("T")[0] if class_item["thoi_gian_tao"] else None

        response = {
            "ma_lop": class_item["ma_lop"],
            "ten_lop": class_item["ten_lop"],
            "ma_so_lop": class_item["ma_so_lop"],
            "ngay_tao": ngay_tao,
            "ngay_bat_dau": class_item["ngay_bat_dau"],
            "ngay_ket_thuc": class_item["ngay_ket_thuc"],
            "ten_dang_nhap": teacher_name,
            "students": students,
            "student_count": student_count
        }

        return response

    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
#xóa giảng viên
@app.delete("/delete_teacher/{ten_dang_nhap}")
async def delete_teacher(
    ten_dang_nhap: str,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (ten_dang_nhap,))
    user = cursor.fetchone()
    if not user or user["vai_tro"] != "giang_vien":
        raise HTTPException(status_code=404, detail="Giảng viên không tồn tại")

    try:
        retry_on_locked(
            db,
            "DELETE FROM nguoi_dung WHERE ten_dang_nhap = ?",
            (ten_dang_nhap,)
        )
        db.commit()
        return {"message": f"Xóa giảng viên {ten_dang_nhap} thành công"}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
#xóa sinh viên 
@app.delete("/delete_student/{ten_dang_nhap}")
async def delete_student(
    ten_dang_nhap: str,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (ten_dang_nhap,))
    user = cursor.fetchone()
    if not user or user["vai_tro"] != "sinh_vien":
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")

    try:
        retry_on_locked(
            db,
            "DELETE FROM nguoi_dung WHERE ten_dang_nhap = ?",
            (ten_dang_nhap,)
        )
        db.commit()
        return {"message": f"Xóa sinh viên {ten_dang_nhap} thành công"}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
#xóa sinh viên khỏi lớp học
@app.delete("/classes/{ma_lop}/students/{student_ten_dang_nhap}/")
async def remove_student_from_class(
    ma_lop: int,
    student_ten_dang_nhap: str,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    # Kiểm tra quyền truy cập (chỉ admin hoặc giảng viên của lớp có quyền)
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()["ma_nguoi_dung"]
    vai_tro = normalize_role(current_user.vai_tro)

    cursor.execute("SELECT ma_giang_vien FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
    class_item = cursor.fetchone()
    if not class_item or (vai_tro == "giang_vien" and class_item["ma_giang_vien"] != ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa sinh viên khỏi lớp này")

    # Kiểm tra xem sinh viên tồn tại và thuộc lớp
    cursor.execute(
        """
        SELECT svlh.ma_sinh_vien_lop_hoc
        FROM sinh_vien_lop_hoc svlh
        JOIN nguoi_dung nd ON svlh.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE svlh.ma_lop = ? AND nd.ten_dang_nhap = ?
        """,
        (ma_lop, student_ten_dang_nhap)
    )
    enrollment = cursor.fetchone()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại trong lớp này")

    # Xóa mối quan hệ sinh viên-lớp
    try:
        retry_on_locked(
            db,
            "DELETE FROM sinh_vien_lop_hoc WHERE ma_sinh_vien_lop_hoc = ?",
            (enrollment["ma_sinh_vien_lop_hoc"],)
        )
        db.commit()
        logger.info(f"Xóa sinh viên {student_ten_dang_nhap} khỏi lớp {ma_lop} thành công")
        return {"message": f"Xóa sinh viên {student_ten_dang_nhap} khỏi lớp {ma_lop} thành công"}
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Lỗi cơ sở dữ liệu khi xóa sinh viên: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
#xóa sinh viên khỏi lớp học
#sửa thông tin sinh viên 
@app.put("/update_student/{ten_dang_nhap}")
async def update_student(
    ten_dang_nhap: str,
    mat_khau: str = Form(None),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (ten_dang_nhap,))
    user = cursor.fetchone()
    if not user or user["vai_tro"] != "sinh_vien":
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")

    try:
        if mat_khau:
            cursor.execute(
                "UPDATE nguoi_dung SET mat_khau = ? WHERE ten_dang_nhap = ?",
                (mat_khau, ten_dang_nhap)
            )
            db.commit()
        return {"message": f"Cập nhật sinh viên {ten_dang_nhap} thành công"}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
    
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.post("/dangky")
async def dang_ky(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    logger.debug(f"Nhận dữ liệu: {user.dict()}")
    
    try:
        normalized_role = normalize_role(user.vai_tro)
        logger.debug(f"Vai trò chuẩn hóa: {normalized_role}")
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    hashed_password = hash_password(user.mat_khau)
    
    if user.email not in VERIFICATION_CODES or VERIFICATION_CODES[user.email]["code"] != user.ma_xac_nhan:
        logger.error("Mã xác nhận không hợp lệ")
        raise HTTPException(status_code=400, detail="Mã xác nhận không hợp lệ")
    
    if datetime.utcnow() > VERIFICATION_CODES[user.email]["expires_at"]:
        logger.error("Mã xác nhận đã hết hạn")
        raise HTTPException(status_code=400, detail="Mã xác nhận đã hết hạn")
    
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, email, vai_tro, trang_thai)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user.ten_dang_nhap, hashed_password, user.email, normalized_role, "cho_duyet")
        )
        db.commit()
        logger.debug("Đã lưu dữ liệu vào cơ sở dữ liệu")
        VERIFICATION_CODES.pop(user.email, None)
        return {"message": "Đăng ký thành công"}
    except sqlite3.IntegrityError as e:
        logger.error(f"Lỗi IntegrityError: {str(e)}")
        raise HTTPException(status_code=400, detail="Email hoặc tên đăng nhập đã tồn tại")
    except Exception as e:
        logger.error(f"Lỗi khác: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
    
#
@app.post("/classes/{ma_lop}/students/")
async def add_student_to_class_id(ma_lop: int, student_data: dict, current_user: UserInDB = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
    class_item = cursor.fetchone()
    if not class_item:
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")

    student_ten_dang_nhap = student_data.get("student_ten_dang_nhap")
    if not student_ten_dang_nhap:
        raise HTTPException(status_code=400, detail="Tên đăng nhập sinh viên không được để trống")

    cursor.execute("SELECT ma_nguoi_dung, vai_tro FROM nguoi_dung WHERE ten_dang_nhap = ? AND vai_tro = 'sinh_vien'", (student_ten_dang_nhap,))
    student = cursor.fetchone()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại hoặc không phải là sinh_vien")
    ma_sinh_vien = student[0]

    cursor.execute("SELECT EXISTS(SELECT 1 FROM sinh_vien_lop_hoc WHERE ma_sinh_vien = ?)", (ma_sinh_vien,))
    if cursor.fetchone()[0]:
        raise HTTPException(status_code=400, detail="Sinh viên đã thuộc một lớp học khác, không thể thêm")

    cursor.execute("SELECT EXISTS(SELECT 1 FROM sinh_vien_lop_hoc WHERE ma_lop = ? AND ma_sinh_vien = ?)", (ma_lop, ma_sinh_vien))
    if cursor.fetchone()[0]:
        raise HTTPException(status_code=400, detail="Sinh viên đã có trong lớp này")

    retry_on_locked(db, "INSERT INTO sinh_vien_lop_hoc (ma_lop, ma_sinh_vien) VALUES (?, ?)", (ma_lop, ma_sinh_vien))
    
    return {
        "message": "Thêm sinh viên thành công",
        "ma_lop": ma_lop,
        "student_ten_dang_nhap": student_ten_dang_nhap
    }

#thay đổi mật khẩu cho giảng viên @app.post("/update_password/")
async def update_password(
    email: str = Form(...),  # Email của người dùng cần đổi mật khẩu
    new_password: str = Form(...),  # Mật khẩu mới
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    if not is_admin(current_user["vai_tro"]):
        raise HTTPException(status_code=403, detail="Chỉ admin có quyền đổi mật khẩu")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM nguoi_dung WHERE ten_dang_nhap = ?", (email,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    # Mã hóa mật khẩu mới
    hashed_password = get_password_hash(new_password)
    
    # Cập nhật mật khẩu trong cơ sở dữ liệu
    retry_on_locked(
        db,
        "UPDATE nguoi_dung SET mat_khau = ? WHERE ten_dang_nhap = ?",
        (hashed_password, email)
    )
    
    return {"message": "Đổi mật khẩu thành công", "ten_dang_nhap": email}


@app.post("/add_student/")
async def add_student(request: UserCreateRequest, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    # Loại bỏ kiểm tra quyền QuanTri
    # if current_user.get("vai_tro") != "QuanTri":
    #     raise HTTPException(status_code=403, detail="Bạn không có quyền thêm sinh viên")
    
    cursor = db.cursor()
    # Kiểm tra email đã tồn tại
    cursor.execute("SELECT EXISTS(SELECT 1 FROM nguoi_dung WHERE email = ?)", (request.email,))
    if cursor.fetchone()[0]:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    
    # Thêm sinh viên
    hashed_password = get_password_hash(request.password)
    cursor.execute(
        "INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, email, vai_tro, trang_thai, thoi_gian_tao) VALUES (?, ?, ?, ?, ?, ?)",
        (request.email.split('@')[0], hashed_password, request.email, "sinh_vien", "cho_duyet", datetime.now().isoformat())
    )
    db.commit()
    return {"message": "Thêm sinh viên thành công"}


@app.post("/update_password/")
async def update_password(
    email: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    if current_user["ten_dang_nhap"] != email:
        if not is_admin(current_user["vai_tro"]):
            raise HTTPException(status_code=403, detail="Chỉ admin hoặc chính chủ có quyền đổi mật khẩu")

    cursor = db.cursor()
    cursor.execute("SELECT mat_khau FROM nguoi_dung WHERE ten_dang_nhap = ? OR email = ?", (email, email))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    stored_password = user[0]
    if not verify_password(current_password, stored_password):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")

    hashed_new_password = get_password_hash(new_password)
    
    retry_on_locked(
        db,
        "UPDATE nguoi_dung SET mat_khau = ? WHERE ten_dang_nhap = ? OR email = ?",
        (hashed_new_password, email, email)
    )
    
    return {"message": "Đổi mật khẩu thành công", "ten_dang_nhap": email}

@app.post("/classes/join/")
async def join_class_by_code(
    ma_so_lop: str = Form(...),
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
#    if current_user.vai_tro != "SinhVien":
#       raise HTTPException(status_code=403, detail="Chỉ sinh viên mới có thể tham gia lớp học")

    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_sinh_vien = cursor.fetchone()["ma_nguoi_dung"]

    cursor.execute("SELECT ma_lop FROM lop_hoc WHERE ma_so_lop = ?", (ma_so_lop,))
    class_item = cursor.fetchone()
    if not class_item:
        raise HTTPException(status_code=404, detail="Mã số lớp không tồn tại")

    ma_lop = class_item["ma_lop"]
    cursor.execute("SELECT EXISTS(SELECT * FROM sinh_vien_lop_hoc WHERE ma_lop = ? AND ma_sinh_vien = ?)", (ma_lop, ma_sinh_vien))
    if cursor.fetchone()[0]:
        raise HTTPException(status_code=400, detail="Bạn đã tham gia lớp này rồi")

    retry_on_locked(
        db,
        "INSERT INTO sinh_vien_lop_hoc (ma_lop, ma_sinh_vien) VALUES (?, ?)",
        (ma_lop, ma_sinh_vien)
    )
    
    return {
        "message": "Tham gia lớp học thành công",
        "ma_lop": ma_lop,
        "ma_so_lop": ma_so_lop
    }

@app.post("/exercises/{ma_bai_tap}/submit/")
async def submit_exercise(
    ma_bai_tap: int,
    submission: str = Form(...),
    submission_file: UploadFile = File(None),
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
#    if current_user.vai_tro != "SinhVien":
#        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới có thể nộp bài tập")

    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_sinh_vien = cursor.fetchone()["ma_nguoi_dung"]

    # Kiểm tra bài tập tồn tại và ở trạng thái mở
    cursor.execute("SELECT trang_thai, han_nop FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    exercise = cursor.fetchone()
    if not exercise:
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    if exercise["trang_thai"] != "mo":
        raise HTTPException(status_code=400, detail="Bài tập đã đóng, không thể nộp")



    # Kiểm tra nội dung nộp bài
    try:
        submission_content = json.loads(submission) if submission else {}
        if not submission_content.get("html") and not submission_content.get("css") and not submission_content.get("js") and not submission_file:
            raise HTTPException(status_code=400, detail="Phải cung cấp ít nhất một nội dung hoặc file nộp bài")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Nội dung nộp bài không hợp lệ")

    # Lưu file đính kèm nếu có
    file_path = None
    if submission_file:
        upload_dir = "frontend/public/uploads/submissions"
        os.makedirs(upload_dir, exist_ok=True)
        file_extension = submission_file.filename.split(".")[-1]
        file_name = f"submission_{ma_bai_tap}_{ma_sinh_vien}.{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(submission_file.file, buffer)
        file_path = f"/uploads/submissions/{file_name}"

    # Xác định trạng thái và lần nộp
    thoi_gian_nop = datetime.now().isoformat()
    han_nop = exercise["han_nop"]
    trang_thai = "nop_tre" if han_nop and thoi_gian_nop > han_nop else "da_nop"

    # Lấy lần nộp hiện tại
    cursor.execute("SELECT lan_nop FROM bai_nop WHERE ma_bai_tap = ? AND ma_sinh_vien = ?", (ma_bai_tap, ma_sinh_vien))
    current_submission = cursor.fetchone()
    lan_nop = (current_submission["lan_nop"] + 1) if current_submission else 1

    # Lưu bài nộp vào bảng bai_nop
    try:
        retry_on_locked(
            db,
            """
            INSERT OR REPLACE INTO bai_nop (
                ma_bai_tap, ma_sinh_vien, noi_dung_nop, tap_tin_nop, thoi_gian_nop, trang_thai, lan_nop
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ma_bai_tap,
                ma_sinh_vien,
                json.dumps(submission_content),
                file_path,
                thoi_gian_nop,
                trang_thai,
                lan_nop
            )
        )
        db.commit()
        return {
            "message": "Nộp bài tập thành công",
            "ma_bai_tap": ma_bai_tap,
            "lan_nop": lan_nop,
            "thoi_gian_nop": thoi_gian_nop,
            "trang_thai": trang_thai
        }
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import json

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import json

@app.get("/exercises/{ma_bai_tap}/submissions/")
async def get_submissions(
    ma_bai_tap: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    # Kiểm tra bài tập tồn tại
    cursor.execute("SELECT * FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")

    # Lấy tất cả bài nộp
    query = """
        SELECT bn.*, nd.ten_dang_nhap
        FROM bai_nop bn
        LEFT JOIN nguoi_dung nd ON bn.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE bn.ma_bai_tap = ?
        ORDER BY bn.thoi_gian_nop DESC
    """
    cursor.execute(query, (ma_bai_tap,))
    
    submissions = cursor.fetchall()
    submission_list = []
    for submission in submissions:
        try:
            noi_dung_nop = json.loads(submission["noi_dung_nop"]) if submission["noi_dung_nop"] else {}
        except json.JSONDecodeError:
            noi_dung_nop = {}
        submission_list.append({
            "ma_bai_nop": submission["ma_bai_nop"],
            "ma_sinh_vien": submission["ma_sinh_vien"],
            "ten_hien_thi": submission["ten_dang_nhap"] or "",
            "noi_dung_nop": noi_dung_nop,
            "tap_tin_nop": submission["tap_tin_nop"],
            "thoi_gian_nop": submission["thoi_gian_nop"],
            "trang_thai": submission["trang_thai"],
            "lan_nop": submission["lan_nop"]
        })
    return submission_list

@app.get("/enrollments/student/{ma_sinh_vien}")
async def get_student_enrollments(ma_sinh_vien: int, token: dict = Depends(verify_token)):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lh.ma_lop, lh.ten_lop, lh.ma_so_lop
            FROM sinh_vien_lop_hoc svlh
            JOIN lop_hoc lh ON svlh.ma_lop = lh.ma_lop
            WHERE svlh.ma_sinh_vien = ? AND svlh.trang_thai = 'hoat_dong' AND lh.trang_thai = 'mo'
        """, (ma_sinh_vien,))
        enrollments = [{"ma_lop": row[0], "ten_lop": row[1], "ma_so_lop": row[2]} for row in cursor.fetchall()]
        conn.close()
        
        return enrollments if enrollments else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/enrollments/teacher/{ma_giang_vien}")
async def get_teacher_enrollments(ma_giang_vien: int, token: dict = Depends(verify_token)):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lh.ma_lop, lh.ten_lop, lh.ma_so_lop
            FROM lop_hoc lh
            WHERE lh.ma_giang_vien = ? AND lh.trang_thai = 'mo'
        """, (ma_giang_vien,))
        enrollments = [{"ma_lop": row[0], "ten_lop": row[1], "ma_so_lop": row[2]} for row in cursor.fetchall()]
        conn.close()
        
        return enrollments if enrollments else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def serve_index():
    file_path = os.path.abspath("frontend/public/index.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File index.html not found")
    return FileResponse(file_path)
@app.get("/taoBT")
async def serve_taoBT():
    return FileResponse("frontend/public/taoBT.html")
@app.get("/themsinhvien")
async def serve_them_sinh_vien():
    file_path = os.path.abspath("frontend/public/themSV.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File themSV.html not found")
    return FileResponse(file_path)

@app.get("/themgiangvien")
async def serve_them_giang_vien():
    file_path = os.path.abspath("frontend/public/themGV.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File themGV.html not found")
    return FileResponse(file_path)

@app.get("/sualophoc")
async def serve_sualophoc(ma_lop: Optional[str] = None, ten_lop: Optional[str] = None, ma_so_lop: Optional[str] = None):
    file_path = os.path.abspath("frontend/public/sualophoc.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File sualophoc.html not found")
    return FileResponse(file_path)

@app.get("/chitietBT")
async def serve_chitietBT():
    file_path = os.path.abspath("frontend/public/chitietBT.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File chitietBT.html not found")
    return FileResponse(file_path)
@app.get("/exercises/{exercise_id}/submissions/{submission_id}/")
async def get_submission_detail(
    exercise_id: int,
    submission_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    # Truy vấn để lấy thông tin bài nộp
    cursor.execute(
        """
        SELECT bn.*, nd.ten_dang_nhap
        FROM bai_nop bn
        LEFT JOIN nguoi_dung nd ON bn.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE bn.ma_bai_tap = ? AND bn.ma_bai_nop = ?
        """,
        (exercise_id, submission_id)
    )
    submission = cursor.fetchone()

    if not submission:
        raise HTTPException(status_code=404, detail="Bài nộp không tồn tại")

    # Xử lý dữ liệu JSON nếu có
    try:
        noi_dung_nop = json.loads(submission["noi_dung_nop"]) if submission["noi_dung_nop"] else {}
    except json.JSONDecodeError:
        noi_dung_nop = {}

    # Trả về dữ liệu dưới dạng từ điển
    return {
        "ma_bai_nop": submission["ma_bai_nop"],
        "ma_bai_tap": submission["ma_bai_tap"],
        "ma_sinh_vien": submission["ma_sinh_vien"],
        "ten_hien_thi": submission["ten_dang_nhap"] or "",
        "noi_dung_nop": noi_dung_nop,
        "tap_tin_nop": submission["tap_tin_nop"],
        "thoi_gian_nop": submission["thoi_gian_nop"],
        "trang_thai": submission["trang_thai"],
        "lan_nop": submission["lan_nop"]
    }
@app.get("/chitietBaiNop")
async def serve_chitiet_bai_nop(ma_bai_tap: int = None, submission_id: str = None):
    file_path = os.path.abspath("frontend/public/chitietBaiNop.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File chitietBaiNop.html not found")
    # Truyền tham số đến template qua query string nếu frontend cần
    if submission_id == "undefined":
        submission_id = None
    return FileResponse(file_path, headers={"ma_bai_tap": str(ma_bai_tap) if ma_bai_tap else "", "submission_id": submission_id if submission_id else ""})

    
@app.get("/exercises/{ma_bai_tap}/submissions/{submission_id}/")
async def get_submission_detail(
    ma_bai_tap: int,
    submission_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    # Thực hiện truy vấn để lấy thông tin bài nộp
    cursor.execute(
        """
        SELECT bn.*, nd.ten_dang_nhap
        FROM bai_nop bn
        LEFT JOIN nguoi_dung nd ON bn.ma_sinh_vien = nd.ma_nguoi_dung
        WHERE bn.ma_bai_tap = ? AND bn.ma_bai_nop = ?
        """,
        (ma_bai_tap, submission_id)
    )
    submission = cursor.fetchone()

    if not submission:
        raise HTTPException(status_code=404, detail="Bài nộp không tồn tại")

    # Xử lý dữ liệu JSON nếu có
    try:
        noi_dung_nop = json.loads(submission["noi_dung_nop"]) if submission["noi_dung_nop"] else {}
    except json.JSONDecodeError:
        noi_dung_nop = {}

    # Trả về dữ liệu dưới dạng từ điển
    return {
        "ma_bai_nop": submission["ma_bai_nop"],
        "ma_bai_tap": submission["ma_bai_tap"],
        "ma_sinh_vien": submission["ma_sinh_vien"],
        "ten_hien_thi": submission["ten_dang_nhap"] or "",
        "noi_dung_nop": noi_dung_nop,
        "tap_tin_nop": submission["tap_tin_nop"],
        "thoi_gian_nop": submission["thoi_gian_nop"],
        "trang_thai": submission["trang_thai"],
        "lan_nop": submission["lan_nop"]
    }  
#lấy số lượng sinh viên nộp bài 

@app.get("/classes/{ma_lop}/exercises/{ma_bai_tap}/submission_status/", response_model=List[StudentSubmissionStatus])
async def get_submission_status(
    ma_lop: int,
    ma_bai_tap: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    
    # Kiểm tra quyền truy cập
    vai_tro = normalize_role(current_user.vai_tro)
    if vai_tro not in ["GiangVien", "QuanTri"]:
        raise HTTPException(status_code=403, detail="Chỉ giảng viên hoặc quản trị viên có quyền xem trạng thái nộp bài")
    
    # Kiểm tra lớp học tồn tại
    cursor.execute("SELECT * FROM lop_hoc WHERE ma_lop = ?", (ma_lop,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Lớp học không tồn tại")
    
    # Kiểm tra bài tập tồn tại
    cursor.execute("SELECT * FROM bai_tap WHERE ma_bai_tap = ?", (ma_bai_tap,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Bài tập không tồn tại")
    
    # Kiểm tra bài tập có được gán cho lớp học không
    cursor.execute(
        "SELECT * FROM bai_tap_lop_hoc WHERE ma_lop = ? AND ma_bai_tap = ?",
        (ma_lop, ma_bai_tap)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Bài tập không thuộc lớp học này")
    
    # Lấy danh sách sinh viên và trạng thái nộp bài
    query = """
        SELECT 
            nd.ma_nguoi_dung,
            nd.ten_dang_nhap,
            COALESCE(bn.trang_thai, 'chua_nop') AS trang_thai_nop,
            bn.thoi_gian_nop,
            bn.lan_nop
        FROM sinh_vien_lop_hoc svlh
        JOIN nguoi_dung nd ON svlh.ma_sinh_vien = nd.ma_nguoi_dung
        LEFT JOIN bai_nop bn ON nd.ma_nguoi_dung = bn.ma_sinh_vien AND bn.ma_bai_tap = ?
        WHERE svlh.ma_lop = ? AND svlh.trang_thai = 'hoat_dong' AND nd.vai_tro = 'sinh_vien'
        ORDER BY nd.ten_dang_nhap
    """
    try:
        cursor.execute(query, (ma_bai_tap, ma_lop))
        students = cursor.fetchall()
        
        submission_status_list = [
            StudentSubmissionStatus(
                ma_sinh_vien=student["ma_nguoi_dung"],
                ten_dang_nhap=student["ten_dang_nhap"],
                trang_thai_nop=student["trang_thai_nop"],
                thoi_gian_nop=student["thoi_gian_nop"],
                lan_nop=student["lan_nop"]
            )
            for student in students
        ]
        
        return submission_status_list
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy trạng thái nộp bài: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")
#lấy số lượng sinh viên nộp bài 
@app.get("/classes/{ma_lop}/assignments/")
async def get_assignments_by_class(
    ma_lop: int,
    current_user: UserInDB = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = ?", (current_user.ten_dang_nhap,))
    ma_nguoi_dung = cursor.fetchone()["ma_nguoi_dung"]

    try: 
        if current_user.vai_tro in ["GiangVien", "QuanTri"]:
            cursor.execute("""
                SELECT bt.*, btlh.ngay_gan, btlh.trang_thai AS trang_thai_lop
                FROM bai_tap bt
                INNER JOIN bai_tap_lop_hoc btlh ON bt.ma_bai_tap = btlh.ma_bai_tap
                WHERE btlh.ma_lop = ? AND bt.ma_giang_vien = ?
                ORDER BY btlh.ngay_gan DESC
            """, (ma_lop, ma_nguoi_dung))
        elif current_user.vai_tro == "SinhVien":
            cursor.execute("""
                SELECT bt.*, btlh.ngay_gan, btlh.trang_thai AS trang_thai_lop
                FROM bai_tap bt
                INNER JOIN bai_tap_lop_hoc btlh ON bt.ma_bai_tap = btlh.ma_bai_tap
                INNER JOIN sinh_vien_lop_hoc svlh ON btlh.ma_lop = svlh.ma_lop
                WHERE btlh.ma_lop = ? AND svlh.ma_sinh_vien = ?
                ORDER BY btlh.ngay_gan DESC
            """, (ma_lop, ma_nguoi_dung))
        else:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem bài tập của lớp này")

        assignments = cursor.fetchall()
        assignment_list = []
        for assignment in assignments:
            try:
                noi_dung = assignment["noi_dung"]
            except json.JSONDecodeError:
                noi_dung = {}
            assignment_list.append({
                "ma_bai_tap": assignment["ma_bai_tap"],
                "ma_giang_vien": assignment["ma_giang_vien"],
                "tieu_de": assignment["tieu_de"],
                "noi_dung": noi_dung,
                "han_nop": assignment["han_nop"],
                "thoi_gian_tao": assignment["thoi_gian_tao"],
                "mo_ta": assignment["mo_ta"],
                "ngon_ngu": assignment["ngon_ngu"],
                "tap_tin_bai_tap": assignment["tap_tin_bai_tap"],
                "trang_thai": assignment["trang_thai"],
                "ngay_gan": assignment["ngay_gan"],
                "trang_thai_lop": assignment["trang_thai_lop"]
            })
        return assignment_list
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cơ sở dữ liệu: {str(e)}")

def authenticate_user(db: sqlite3.Connection, username_or_email: str, password: str):
    cursor = db.cursor()
    cursor.execute(
        "SELECT ma_nguoi_dung, ten_dang_nhap, mat_khau, vai_tro, email FROM nguoi_dung WHERE ten_dang_nhap = ? OR email = ?",
        (username_or_email, username_or_email)
    )
    user = cursor.fetchone()
    if not user:
        logger.debug(f"User not found: {username_or_email}")
        return None
    stored_hash = user["mat_khau"]
    if not pwd_context.verify(password, stored_hash):
        logger.debug(f"Password verification failed for {username_or_email}")
        return None
    logger.debug(f"Authentication successful for {username_or_email} with role {user['vai_tro']}")
    return {
        "ma_nguoi_dung": user["ma_nguoi_dung"],
        "ten_dang_nhap": user["ten_dang_nhap"],
        "vai_tro": user["vai_tro"],
        "email": user["email"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)