import sqlite3
import json

DB_PATH = "backend/check_results.db"

def create_table():
    """Tạo bảng lưu lịch sử kiểm tra nếu chưa có"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            html TEXT,
            css TEXT,
            js TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_check_result(html, css, js, result):
    """Lưu kết quả kiểm tra vào database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO results (html, css, js, result) VALUES (?, ?, ?, ?)", 
                   (html, css, js, json.dumps(result)))
    conn.commit()
    conn.close()

def get_history():
    """Lấy danh sách lịch sử kiểm tra"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, html, css, js, result, timestamp FROM results ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "html": row[1],
            "css": row[2],
            "js": row[3],
            "result": json.loads(row[4]),
            "timestamp": row[5]
        })
    
    return history

# Gọi hàm tạo bảng khi module được import
create_table()
