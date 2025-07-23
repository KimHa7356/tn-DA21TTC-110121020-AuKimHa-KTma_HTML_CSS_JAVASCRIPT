# tn-DA21TTC-110121020-AuKimHa-KTma_HTML_CSS_JAVASCRIPT

## XÂY DỰNG CÔNG CỤ ĐÁNH GIÁ CHẤT LƯỢNG MÃ HTML, CSS, JAVASCREIPT

### Giảng viên hướng dẫn

- Nguyễn Ngọc Đan Thanh
- Email: ngocdanthanhdt@tvu.edu.vn

### Sinh viên thực hiện

- Âu Kim Hà
- Email: kimha7356@gmail.com
- Số điện thoại: 0393587915

## MỤC TIÊU

- Xây dựng một công cụ tự động phân tích và đánh giá chất lượng mã nguồn HTML, CSS, và JavaScript.
- Hỗ trợ người dùng phát hiện lỗi cú pháp, tối ưu hóa hiệu suất, và tuân thủ các quy chuẩn lập trình.
- Cung cấp giao diện thân thiện và phản hồi chi tiết để cải thiện kỹ năng lập trình.

## KIẾN TRÚC

- Frontend: Sử dụng HTML, CSS (Tailwind CSS), và JAVASCRIPT để xây dựng giao diện người dùng trực quan.
- Backend: Xây dựng bằng FastAPI, tích hợp các công cụ phân tích mã nguồn và cung cấp phản hồi chi tiết.

## PHẦN MỀM CẦN THIẾT

- Node.js: Để biên dịch và chạy các công cụ phân tích mã như ESLint.
- Python 3.x: Cài đặt FastAPI và các thư viện liên quan
- pip: Để quản lý các gói Python
- Git: Để clone và quản lý mã nguồn từ repository.

## CÁCH THỨC CHẠY CHƯƠNG TRÌNH

- 1.Clone Repository:
- Mở terminal hoặc command prompt
- Chạy lệnh sau để tải mã nguồn từ GitHub
  - git clone https://github.com/KimHa7356/tn-DA21TTC-110121020-AuKimHa-KTma_HTML_CSS_JAVASCRIPT.git
- Di chuyển vào thư mục dự án vừa clone:
  - cd tn-DA21TTC-110121020-AuKimHa-KTma_HTML_CSS_JAVASCRIPT
- 2.Chạy Backend
- Mở terminal, di chuyển đến thư mục dự án, và chạy server FastAPI:
  - uvicorn main:app --reload
- Mở Frontend
  - http://127.0.0.1:8000
