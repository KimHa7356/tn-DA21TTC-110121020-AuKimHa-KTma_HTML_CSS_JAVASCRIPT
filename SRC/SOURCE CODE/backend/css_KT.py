import cssutils
import logging
import re
from typing import Dict, List, Optional
import xml.dom

# Khởi tạo logger cho module này
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Cấu hình logging ở mức INFO

# Danh sách thuộc tính CSS hợp lệ
# Danh sách thuộc tính CSS hợp lệ
CSS_PROPERTIES = [
    "background", "background-color", "border", "color", "display", "font",
    "font-family", "font-size", "font-weight", "height", "width", "margin", "padding",
    "padding-top", "position", "text-align", "top", "left", "right", "bottom", "z-index",
    "opacity", "overflow", "visibility", "line-height", "max-width", "min-width",
    "text-decoration", "border-radius", "box-shadow", "transition", "cursor"
]

def suggest_property_name(prop_name: str) -> Optional[str]:
    """Gợi ý tên thuộc tính CSS gần đúng."""
    from difflib import get_close_matches
    matches = get_close_matches(prop_name.lower(), [p.lower() for p in CSS_PROPERTIES], n=1)
    return matches[0] if matches else None

def check_brackets_balance(css_code: str) -> List[Dict[str, any]]:
    """Kiểm tra sự cân bằng của dấu { và } trong mã CSS."""
    errors = []
    lines = css_code.split("\n")
    open_brackets = 0
    last_open_line = 0

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        open_brackets += line.count("{")
        if "{" in line:
            last_open_line = i
        open_brackets -= line.count("}")

        if open_brackets < 0:
            errors.append({
                "type": "Lỗi cú pháp",
                "message": "Dấu } dư thừa, không có dấu { tương ứng.",
                "line": i,
                "language": "CSS",
                "suggestion": "Xóa dấu } dư thừa hoặc kiểm tra khối CSS."
            })
            break

    if open_brackets > 0:
        errors.append({
            "type": "Lỗi cú pháp",
            "message": "Thiếu dấu } để đóng khối CSS.",
            "line": last_open_line,
            "language": "CSS",
            "suggestion": "Thêm dấu } để đóng khối CSS. Ví dụ: h1 { color: red; }"
        })

    return errors

def check_css(css_code: str, is_inline: bool = False) -> Dict[str, any]:
    """
    Kiểm tra cú pháp CSS và trả về danh sách lỗi (nếu có).
    Args:
        css_code (str): Mã CSS cần kiểm tra.
        is_inline (bool): Xác định CSS là inline (trong thẻ style).
    Returns:
        dict: Trạng thái, danh sách lỗi và mã đã sửa (nếu có).
    """
    errors = []
    fixed_code = css_code.strip()

    if not css_code.strip():
        return {"status": "✅ Mã CSS hợp lệ", "errors": errors, "fixed_code": fixed_code}

    # Kiểm tra sự cân bằng của dấu { và }
    if not is_inline:
        errors.extend(check_brackets_balance(css_code))

    # Nếu đã có lỗi từ check_brackets_balance, trả về ngay
    if errors:
        return {"status": "❌ Mã CSS có lỗi", "errors": errors, "fixed_code": fixed_code}

    # Kiểm tra lồng selector bằng regex
    nested_selector_pattern = r'([^{}]+)\s*{[^{}]*{[^{}]*}'
    nested_matches = re.finditer(nested_selector_pattern, css_code)
    for match in nested_matches:
        errors.append({
            "type": "Lỗi cú pháp",
            "message": "Bạn đang dùng cú pháp lồng selector, không hợp lệ trong CSS chuẩn.",
            "line": css_code[:match.start()].count('\n') + 1,
            "language": "CSS",
            "suggestion": "CSS chuẩn không hỗ trợ lồng selector."
        })

    # Phân tích cú pháp bằng cssutils
    parser = cssutils.CSSParser(raiseExceptions=True)
    try:
        parse_code = css_code if is_inline else css_code
        if is_inline:
            parse_code = f"dummy {{ {css_code} }}"
        sheet = parser.parseString(parse_code)
        if not sheet.cssRules and css_code.strip() and not errors and not is_inline:
            errors.append({
                "type": "Lỗi cú pháp",
                "message": "Mã CSS không hợp lệ, không tìm thấy quy tắc nào.",
                "line": 1,
                "language": "CSS",
                "suggestion": "Kiểm tra cú pháp CSS, đảm bảo định dạng đúng. Ví dụ: h1 { color: red; }"
            })
    except (xml.dom.SyntaxErr, Exception) as e:
        error_msg = str(e)
        line_number = e.line - 1 if is_inline and hasattr(e, 'line') else (e.line if hasattr(e, 'line') else 1)
        # Chỉ thêm lỗi cú pháp chung nếu chưa có lỗi lồng selector
        if not any("lồng selector" in error["message"].lower() for error in errors) and \
        not any("thiếu giá trị" in error["message"].lower() for error in errors) and \
        "no content to parse" not in error_msg.lower():
            errors.append({
                "type": "Lỗi cú pháp",
                "message": "Có lỗi trong cách sắp xếp mã CSS, hãy kiểm tra lại nhé!",
                "line": line_number,
                "language": "CSS",
                "suggestion": "Kiểm tra cú pháp CSS, đảm bảo không có dấu ngoặc hoặc định dạng sai."
            })

    # Kiểm tra thuộc tính và giá trị
    lines = css_code.split("\n")
    inside_block = False if not is_inline else True
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        if not is_inline and "{" in line:
            inside_block = True
            continue
        if not is_inline and "}" in line:
            inside_block = False
            continue
        if ":" in line:
            declarations = [d.strip() for d in line.split(";") if d.strip()]
            for decl in declarations:
                if ":" in decl:
                    prop, value = [p.strip() for p in decl.split(":", 1)]
                    if prop and prop.lower() not in [p.lower() for p in CSS_PROPERTIES]:
                        suggestion = suggest_property_name(prop)
                        if prop.lower() == "colour":
                            msg = f"Thuộc tính CSS '{prop}' sai chính tả."
                            sugg_text = f"Thay '{prop}' bằng 'color'."
                            fixed_code = fixed_code.replace(prop, "color")
                        else:
                            msg = f"Thuộc tính '{prop}' không hợp lệ hoặc không được hỗ trợ."
                            sugg_text = "Tên thuộc tính này không có trong danh sách CSS chuẩn. \n Hãy kiểm tra lại chính tả hoặc thay thế bằng thuộc tính hợp lệ như color."
                            if suggestion:
                                sugg_text = f"Thay '{prop}' bằng '{suggestion}'."
                                fixed_code = fixed_code.replace(prop, suggestion)
                        errors.append({
                            "type": "Lỗi cú pháp",
                            "message": msg,
                            "line": i,
                            "language": "CSS",
                            "suggestion": sugg_text
                        })

                    if not value and not is_inline:
                        if prop.lower() == "color":
                            errors.append({
                                "type": "Thiếu giá trị",
                                "message": "Thuộc tính color thiếu giá trị",
                                "line": i,
                                "language": "CSS",
                                "suggestion": "Thêm giá trị màu hợp lệ cho color\nVí dụ:\ncolor: red; \n color: #ff0000;"
                            })
                            fixed_code = fixed_code.replace(f"{prop}:", f"{prop}: red;", 1)
                        else:
                            errors.append({
                                "type": "Thiếu giá trị",
                                "message": f"Thuộc tính '{prop}' thiếu giá trị.",
                                "line": i,
                                "language": "CSS",
                                "suggestion": f"Thêm giá trị cho thuộc tính '{prop}'. Ví dụ:\nTrước: {prop}:\nSau: {prop}: 16px;"
                            })
                            fixed_code = fixed_code.replace(f"{prop}:", f"{prop}: 16px;", 1)

            # Kiểm tra thiếu dấu chấm phẩy (;)
            if not is_inline and inside_block and ":" in line and not line.endswith(";"):
                is_last_declaration = False
                for j in range(i, len(lines)):
                    if "}" in lines[j].strip():
                        is_last_declaration = True
                        break
                prop_value = line.strip()
                if not is_last_declaration:
                    errors.append({
                        "type": "Lỗi cú pháp",
                        "message": f"Thiếu dấu chấm phẩy (;) sau khai báo '{prop_value}'.",
                        "line": i,
                        "language": "CSS",
                        "suggestion": f"Thêm dấu chấm phẩy (;) để phân tách các khai báo CSS.\nVí dụ:\nTrước: {prop_value}\nSau: {prop_value};"
                    })
                    fixed_code = fixed_code.replace(prop_value, f"{prop_value};", 1)
                else:
                    errors.append({
                        "type": "Lỗi cú pháp",
                        "message": f"Thiếu dấu chấm phẩy (;) sau khai báo '{prop_value}'.",
                        "line": i,
                        "language": "CSS",
                        "suggestion": f"Thêm dấu chấm phẩy (;) để đảm bảo tính nhất quán.\nVí dụ:\nTrước: {prop_value}\nSau: {prop_value};"
                    })
                    fixed_code = fixed_code.replace(prop_value, f"{prop_value};", 1)

    # Loại bỏ lỗi trùng lặp
    seen_errors = set()
    unique_errors = []
    for error in errors:
        error_key = (error["type"], error["message"], error["line"])
        if error_key not in seen_errors:
            seen_errors.add(error_key)
            unique_errors.append(error)

    status = "✅ Mã CSS hợp lệ" if not unique_errors else "❌ Mã CSS có lỗi"
    return {"status": status, "errors": unique_errors, "fixed_code": fixed_code}