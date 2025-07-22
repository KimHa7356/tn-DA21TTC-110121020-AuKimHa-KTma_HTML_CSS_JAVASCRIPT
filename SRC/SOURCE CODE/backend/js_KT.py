import re
import subprocess
import json
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def translate_eslint_message(message: str, var_name: str = "", line_content: str = "") -> str:
    """Dịch thông báo lỗi ESLint hoặc Node.js sang tiếng Việt."""
    message_lower = message.lower()
    if "is defined but never used" in message_lower:
        return f"{'Hàm' if 'function' in message_lower else 'Biến'} '{var_name}' được định nghĩa nhưng không được sử dụng."
    elif "is assigned a value but never used" in message_lower:
        return f"Biến '{var_name}' được gán giá trị nhưng không được sử dụng."
    elif "unexpected console statement" in message_lower:
        return "Câu lệnh console không mong muốn."
    elif "missing semicolon" in message_lower:
        return "Thiếu dấu chấm phẩy."
    elif "unexpected token" in message_lower or "unexpected identifier" in message_lower or "unterminated string literal" in message_lower:
        if "console.log" in line_content and "(" in line_content and ")" not in line_content:
            return f"Thiếu dấu đóng ngoặc ) trong {line_content.strip()}"
        return f"Lỗi cú pháp trong dòng: {line_content.strip()}"
    # Loại bỏ đường dẫn file từ thông báo Node.js
    if "temp.js" in message_lower:
        return f"Lỗi cú pháp trong dòng: {line_content.strip()}"
    return message

def check_js(js_code: str, used_functions: set = None):
    errors = []
    fixed_code = js_code.rstrip()  # Chỉ xóa khoảng trắng ở cuối, giữ dòng trống ở đầu
    js_content = fixed_code

    if not js_content.strip():
        return {
            "status": "Không tìm thấy mã JavaScript",
            "errors": [{"type": "Lỗi", "message": "Không có mã JavaScript để kiểm tra.", "line": "N/A", "suggestion": "Nhập mã JavaScript hoặc kiểm tra thẻ <script>.", "language": "JavaScript"}],
            "fixed_code": js_content,
            "html_content": "",
            "language": "JavaScript"
        }

    # Chuẩn hóa thụt lề và đếm dòng chính xác
    lines = js_content.splitlines()
    normalized_lines = [line.rstrip() for line in lines]
    js_content = "\n".join(normalized_lines) + "\n"

    # Kiểm tra cú pháp ban đầu: phát hiện câu lệnh thiếu ngoặc đóng
    for i, line in enumerate(normalized_lines, 1):
        if "console.log" in line.lower() and "(" in line and ")" not in line:
            errors.append({
                "type": "Lỗi cú pháp",
                "message": f"Thiếu dấu ngoặc đóng ) trong {line.strip()}",
                "line": i,
                "suggestion": f"Thêm dấu ngoặc đóng ) và dấu chấm phẩy ; vào {line.strip()} tại dòng {i}.",
                "language": "JavaScript"
            })
            # Tự động sửa lỗi (thêm ngoặc và dấu ;)
            fixed_code = fixed_code[:fixed_code.rfind(line)] + line.rstrip() + ");" + fixed_code[fixed_code.rfind(line) + len(line):]
            js_content = fixed_code

    # Kiểm tra cú pháp bằng Node.js
    try:
        temp_file = "temp.js"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(js_content)

        result = subprocess.run(
            ["node", "-c", temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            error_msg = result.stderr
            line_match = re.search(r"temp\.js:(\d+):(\d+)", error_msg)
            temp_line_num = 1
            if line_match:
                temp_line_num = int(line_match.group(1))

            # Tìm dòng lỗi chính xác
            editor_line_num = temp_line_num
            line_content = normalized_lines[temp_line_num - 1] if temp_line_num <= len(normalized_lines) else ""
            # Ưu tiên kiểm tra lỗi thiếu ngoặc
            for i, line in enumerate(normalized_lines, 1):
                if "console.log" in line and "(" in line and ")" not in line:
                    editor_line_num = i
                    line_content = line
                    break
                elif re.search(r"[^\s;]\s*$", line.strip()) and "{" not in line and "}" not in line:
                    editor_line_num = i
                    line_content = line
                    break

            suggestion = (
                f"Thêm dấu ngoặc đóng ) và dấu chấm phẩy ; vào {line_content.strip()} tại dòng {editor_line_num}."
                if "console.log" in line_content and "(" in line_content and ")" not in line_content
                else f"Kiểm tra cú pháp của {line_content.strip()} tại dòng {editor_line_num} (có thể thiếu ngoặc hoặc dấu chấm phẩy)."
            )

            # Chỉ thêm lỗi nếu chưa được phát hiện trước đó
            if not any(error["line"] == editor_line_num and "Thiếu dấu ngoặc đóng" in error["message"] for error in errors):
                errors.append({
                    "type": "Lỗi cú pháp",
                    "message": translate_eslint_message(error_msg, line_content=line_content),
                    "line": editor_line_num,
                    "suggestion": suggestion,
                    "language": "JavaScript"
                })

            if os.path.exists(temp_file):
                os.remove(temp_file)

            # Dừng kiểm tra nếu có lỗi cú pháp nghiêm trọng
            if errors:
                return {
                    "status": "JavaScript lỗi",
                    "errors": errors,
                    "fixed_code": js_content,
                    "html_content": "",
                    "language": "JavaScript"
                }

        if os.path.exists(temp_file):
            os.remove(temp_file)

    except subprocess.TimeoutExpired:
        errors.append({
            "type": "Lỗi hệ thống",
            "message": "Kiểm tra cú pháp bị quá thời gian xử lý.",
            "line": "N/A",
            "suggestion": "Đơn giản hóa mã JS hoặc kiểm tra lại.",
            "language": "JavaScript"
        })
        return {
            "status": "JavaScript lỗi",
            "errors": errors,
            "fixed_code": js_content,
            "html_content": "",
            "language": "JavaScript"
        }
    except Exception as e:
        errors.append({
            "type": "Lỗi hệ thống",
            "message": f"Lỗi không xác định: {str(e)}",
            "line": "N/A",
            "suggestion": "Kiểm tra cài đặt Node.js.",
            "language": "JavaScript"
        })
        return {
            "status": "JavaScript lỗi",
            "errors": errors,
            "fixed_code": js_content,
            "html_content": "",
            "language": "JavaScript"
        }

    # ... (phần còn lại của hàm check_js giữ nguyên)

    # Kiểm tra cú pháp bằng đếm dấu ngoặc
    lines = js_content.splitlines()
    open_braces = 0
    function_stack = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.search(r"\bfunction\b", stripped, re.IGNORECASE):
            function_stack.append(i)
        open_braces += stripped.count("{")
        open_braces -= stripped.count("}")
        if open_braces < 0:
            open_braces = 0
            function_stack = []

    if open_braces > 0 and function_stack:
        errors.append({
            "type": "Lỗi cú pháp",
            "message": "Thiếu dấu } để đóng hàm.",
            "line": function_stack[-1],
            "suggestion": "Thêm dấu } để đóng hàm function.",
            "language": "JavaScript"
        })
        js_content += "\n}"

    # Chạy ESLint
    try:
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        config_path = os.path.join(frontend_dir, "eslint.config.mjs")
        node_modules_path = os.path.join(frontend_dir, "node_modules")
        eslint_path = os.path.join(node_modules_path, ".bin", "eslint" + (".cmd" if os.name == "nt" else ""))

        if not os.path.exists(node_modules_path) or not os.path.exists(eslint_path):
            return {
                "status": "Lỗi: Thiếu node_modules hoặc eslint",
                "errors": [{"type": "Lỗi hệ thống", "message": "Thiếu node_modules hoặc eslint. Chạy 'npm install' trong thư mục frontend.", "line": "N/A", "suggestion": "Chạy 'npm install' trong thư mục frontend.", "language": "JavaScript"}],
                "fixed_code": js_content,
                "html_content": "",
                "language": "JavaScript"
            }

        result = subprocess.run(
                [eslint_path, "--stdin", "--format=json", "--config", config_path],
                input=js_content,
                capture_output=True,
                text=True,
                cwd=frontend_dir,
                timeout=10
            )

        if result.returncode != 0 and not result.stdout.strip():
                return {
                    "status": "Lỗi khi chạy ESLint",
                    "errors": [{"type": "Lỗi hệ thống", "message": "Không có đầu ra từ ESLint.", "line": "N/A", "suggestion": "Kiểm tra lại cấu hình ESLint hoặc chạy 'npm install'.", "language": "JavaScript"}],
                    "fixed_code": js_content,
                    "html_content": "",
                    "language": "JavaScript"
                }

        eslint_output = json.loads(result.stdout)
        processed_errors = set()

        for file_report in eslint_output:
            for error in file_report.get("messages", []):
                line = error.get("line", "N/A")
                try:
                    line = int(line)
                    if line > len(lines) or line < 1:
                        continue
                except:
                    line = "N/A"

                message = error["message"]
                rule_id = error.get("ruleId", "")
                var_name = message.split("'")[1] if "'" in message and rule_id in ["no-undef", "no-unused-vars"] else ""
                line_content = lines[line - 1] if isinstance(line, int) and 0 < line <= len(lines) else ""
                translated_message = translate_eslint_message(message, var_name, line_content)
                # Sử dụng tuple chi tiết hơn để tránh trùng lặp
                error_key = (translated_message, line, rule_id)

                if error_key in processed_errors:
                    continue

                if rule_id == "no-unused-vars" and used_functions and var_name in used_functions:
                    continue

                suggestion = (
                    f"Xóa hoặc sử dụng {'hàm' if rule_id == 'no-unused-vars' and var_name == 'test' else 'biến'} '{var_name}' trong mã."
                    if rule_id == "no-unused-vars"
                    else "Xóa câu lệnh console hoặc bật tùy chọn cho phép console trong ESLint."
                    if "unexpected console statement" in message.lower()
                    else "Thêm dấu chấm phẩy ở cuối câu lệnh."
                    if "missing semicolon" in message.lower()
                    else f"Thêm dấu ngoặc đóng ) và dấu chấm phẩy ; vào {line_content.strip()} tại dòng {line}."
                    if "unexpected token" in message.lower() and "console.log" in line_content
                    else "Thêm dấu ngoặc đóng ) hoặc dấu chấm phẩy ; cho câu lệnh."
                    if "unexpected token" in message.lower()
                    else "Tham khảo thêm tại https://eslint.org/docs/latest/rules/."
                )
                error_detail = {
                    "type": "Lỗi cú pháp" if error["severity"] == 2 else "Cảnh báo",
                    "message": translated_message,
                    "line": line,
                    "suggestion": suggestion,
                    "language": "JavaScript"
                }

                if rule_id:
                    error_detail["rule"] = rule_id

                errors.append(error_detail)
                processed_errors.add(error_key)
                

    except subprocess.TimeoutExpired:
        return {
            "status": "ESLint Timeout",
            "errors": [{"type": "Lỗi hệ thống", "message": "Lệnh ESLint bị quá thời gian xử lý.", "line": "N/A", "suggestion": "Kiểm tra cấu hình hoặc đơn giản hóa mã JS.", "language": "JavaScript"}],
            "fixed_code": js_content,
            "html_content": "",
            "language": "JavaScript"
        }
    except Exception as e:
        return {
            "status": "Lỗi không xác định",
            "errors": [{"type": "Lỗi hệ thống", "message": f"Lỗi không xác định: {str(e)}", "line": "N/A", "suggestion": "Kiểm tra mã hoặc cấu hình ESLint.", "language": "JavaScript"}],
            "fixed_code": js_content,
            "html_content": "",
            "language": "JavaScript"
        }

    return {
        "status": "JavaScript hợp lệ" if not errors else "JavaScript lỗi",
        "errors": errors,
        "fixed_code": js_content,
        "html_content": "",
        "language": "JavaScript"
    }

if __name__ == "__main__":
    js_code = """
function myFunction() {
    let unusedVar = 42;
    console.log("Hello"
        let x = 6;
    unusedVar = 100;
}
function unusedFunction() {
    let anotherVar = "Test";
    console.log("Unused function");
}
let globalVar = 10;
console.log("Global", globalVar
      function brokenFunction() {
        return "Broken";
    }
"""
    result = check_js(js_code)
    print(json.dumps(result, indent=2, ensure_ascii=False))