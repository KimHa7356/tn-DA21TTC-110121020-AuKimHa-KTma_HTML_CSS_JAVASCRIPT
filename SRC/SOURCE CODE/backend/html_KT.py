import re
from bs4 import BeautifulSoup
from lxml import etree

# Danh sách thẻ HTML hợp lệ
valid_html_tags = {
    "html", "head", "body", "title", "meta", "link", "script", "style",
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "ul", "ol", "li", "strong", "em", "table", "tr", "td", "th",
    "form", "input", "button", "label", "select", "option", "textarea",
    "br", "hr", "nav", "section", "article", "aside", "footer", "header",
    "main", "figure", "figcaption", "time", "mark", "cite", "code", "pre",
    "blockquote", "dl", "dt", "dd", "menu", "menuitem", "canvas", "iframe",
    "audio", "video", "source", "track", "embed", "object", "param"
}

self_closing_tags = {
    "meta", "link", "img", "br", "hr", "input", "source", "track", "embed", "param"
}

def translate_w3c_message(message: str):
    """Dịch thông báo lỗi W3C sang tiếng Việt và cung cấp gợi ý sửa."""
    message_lower = message.lower()
    if "no document type declaration" in message_lower:
        return "Thiếu khai báo &lt;!DOCTYPE html&gt;.", "Thêm &lt;!DOCTYPE html&gt; vào dòng đầu tiên của tài liệu để tuân thủ chuẩn HTML5."
    elif "misplaced doctype declaration" in message_lower:
        return "Khai báo DOCTYPE nằm sai vị trí.", "Di chuyển &lt;!DOCTYPE html&lt; lên dòng đầu tiên của tài liệu HTML."
    elif "end tag" in message_lower:
        tag_match = re.search(r'end tag for "([^"]+)"', message_lower)
        tag = tag_match.group(1) if tag_match else "thẻ"
        return f"Thiếu thẻ đóng cho &lt;{tag}&gt;.", f"Thêm thẻ đóng &lt;/{tag}&lt; để hoàn thiện cấu trúc."
    elif "attribute" in message_lower and "lang" in message_lower:
        return "Thẻ html thiếu thuộc tính lang để xác định ngôn ngữ.", "Thêm lang=\"vi\" vào thẻ html."
    elif "attribute" in message_lower:
        attr_match = re.search(r'attribute "([^"]+)"', message_lower)
        attr = attr_match.group(1) if attr_match else "không xác định"
        return f"Thuộc tính '{attr}' không hợp lệ.", f"Xóa hoặc sửa thuộc tính '{attr}' để tuân thủ chuẩn."
    elif "element" in message_lower and "not allowed" in message_lower:
        return "Thẻ không được phép ở vị trí này.", "Kiểm tra vị trí thẻ hoặc xóa thẻ không hợp lệ để sửa lỗi."
    elif "external resource" in message_lower or "script" in message_lower:
        return "Tài nguyên bên ngoài lỗi.", "Kiểm tra URL của tài nguyên để đảm bảo hoạt động."
    elif "syntax error" in message_lower or "parse error" in message_lower:
        return "Lỗi cú pháp HTML.", "Kiểm tra cú pháp HTML để đảm bảo tất cả thẻ được đóng đúng."
    else:
        return "Lỗi không xác định.", "Kiểm tra mã HTML theo chuẩn HTML5 để xác định vấn đề."

def check_lxml(html_code: str, original_lines: int):
    errors = []
    lines = html_code.split("\n")
    
    for i, line in enumerate(lines, 1):
        open_matches = re.findall(r'<([a-zA-Z][a-zA-Z0-9\-]*)\b[^>]*>', line.lower())
        for tag in open_matches:
            if tag not in valid_html_tags and tag not in self_closing_tags:
                errors.append({
                    "type": "Thẻ không hợp lệ",
                    "message": f"Thẻ {tag} không hợp lệ.",
                    "line": i,
                    "highlight_line": i,
                    "suggestion": f"Thẻ {tag} không phải là thẻ hợp lệ trong HTML5. Thay thế bằng thẻ hợp lệ như &lt;div&gt; hoặc &lt;span&gt; để tuân thủ chuẩn.",
                    "language": "HTML"
                })
    
    try:
        parser = etree.HTMLParser(recover=False)
        tree = etree.fromstring(html_code, parser)
        
        for element in tree.iter():
            tag = element.tag
            if callable(tag):
                continue
            if tag not in valid_html_tags:
                reported_line = element.sourceline or "N/A"
                if reported_line != "N/A" and isinstance(reported_line, int):
                    if reported_line > original_lines or reported_line <= 0:
                        continue
                    adjusted_line = reported_line
                else:
                    adjusted_line = "N/A"
                errors.append({
                    "type": "Thẻ không hợp lệ",
                    "message": f"Thẻ &lt;{tag}&gt; không hợp lệ.",
                    "line": adjusted_line,
                    "highlight_line": adjusted_line if adjusted_line != "N/A" else None,
                    "suggestion": "Thẻ <&lt;{tag}&gt;> không phải là thẻ hợp lệ trong HTML5. Thay thế bằng thẻ hợp lệ như <div> hoặc <span> để tuân thủ chuẩn.",
                    "language": "HTML"
                })
        
        for element in tree.iter():
            if callable(element.tag):
                continue
            seen_attrs = set()
            # Danh sách các thuộc tính hợp lệ chung cho tất cả thẻ
            common_valid_attrs = {"id", "class", "style", "title", "lang", "dir", "data-*", "aria-*", "role"}
            # Các thuộc tính cụ thể cho từng thẻ
            specific_valid_attrs = {
                "meta": {"charset", "name", "content", "http-equiv"},
                "html": {"lang", "dir", "manifest"},
                "title": set(),
                "h1": {"id", "class", "style", "title", "data-*"},
                "button": {"id", "class", "style", "data-*", "onclick", "type", "disabled", "value"},
                "p": {"id", "class", "style", "title", "lang", "dir", "data-*"},  # Thêm thẻ <p>
                # Có thể thêm các thẻ khác nếu cần
            }
            valid_attrs = specific_valid_attrs.get(element.tag, common_valid_attrs)
            for attr in element.attrib:
                reported_line = element.sourceline or "N/A"
                if reported_line == "N/A" or (isinstance(reported_line, int) and reported_line > original_lines):
                    continue
                adjusted_line = reported_line
                if attr in seen_attrs:
                    errors.append({
                        "type": "Thuộc tính trùng lặp",
                        "message": f"Thuộc tính '{attr}' trùng lặp trong thẻ <{element.tag}>.",
                        "line": adjusted_line,
                        "highlight_line": adjusted_line if isinstance(adjusted_line, int) and adjusted_line <= original_lines else None,
                        "suggestion": f"Xóa thuộc tính '{attr}' trùng lặp để tránh xung đột.",
                        "language": "HTML"
                    })
                elif attr not in valid_attrs and not attr.startswith("data-") and not attr.startswith("aria-"):
                    errors.append({
                        "type": "Thuộc tính không hợp lệ",
                        "message": f"Thuộc tính '{attr}' không hợp lệ trong thẻ <{element.tag}>.",
                        "line": adjusted_line,
                        "highlight_line": adjusted_line if isinstance(adjusted_line, int) and adjusted_line <= original_lines else None,
                        "suggestion": f"Xóa hoặc thay thế thuộc tính '{attr}' bằng một thuộc tính hợp lệ như 'id', 'class'.",
                        "language": "HTML"
                    })
                seen_attrs.add(attr)

    except etree.ParseError as e:
        error_line = "N/A"
        error_message = str(e).replace('(<string>, line', '(dòng')
        error_match = re.search(r'line (\d+)', str(e))
        if error_match:
            reported_line = int(error_match.group(1))
            if 1 <= reported_line <= original_lines:
                error_line = reported_line
        if "misplaced doctype declaration" in error_message.lower():
            pass
        elif "misplaced html tag" in error_message.lower():
            # Loại bỏ thẻ <html> thừa bằng cách giữ chỉ một cặp thẻ hợp lệ
            fixed_lines = []
            inside_html = False
            for i, line in enumerate(lines, 1):
                if re.search(r'<\s*html\b', line, re.IGNORECASE) and not inside_html:
                    inside_html = True
                    fixed_lines.append(line)
                elif re.search(r'</\s*html\s*>', line, re.IGNORECASE) and inside_html:
                    inside_html = False
                    fixed_lines.append(line)
                elif inside_html:
                    fixed_lines.append(line)
            html_code = "\n".join(fixed_lines).strip()
            # Thử phân tích lại mà không báo lỗi
            try:
                tree = etree.fromstring(html_code, etree.HTMLParser(recover=False))
            except etree.ParseError:
                pass  # Nếu vẫn lỗi, bỏ qua và tiếp tục
    return errors
    

def check_html(html_code: str):
    errors = []
    # Khởi tạo danh sách lỗi và chuẩn hóa mã HTML đầu vào
    fixed_code = html_code.strip() # Loại bỏ khoảng trắng thừa ở đầu/cuối
    lines = html_code.split("\n") # Tách mã HTML thành các dòng
    original_lines = len(lines)# Lưu số dòng ban đầu để kiểm tra lỗi
    print("📌 DEBUG: HTML đầu vào:\n", html_code) # In mã đầu vào để debug

    # Biến để lưu nội dung CSS từ thẻ <style>
    css_content = ""
    style_start_line = None
    for i, line in enumerate(lines, 1):
        if "<style" in line.lower():
            style_start_line = i
        elif style_start_line and "</style>" in line.lower():
            css_lines = lines[style_start_line-1:i]
            css_content = "\n".join(line.strip() for line in css_lines if "<style" not in line.lower() and "</style>" not in line.lower()).strip()
            style_start_line = None
        elif style_start_line and "<style" not in line.lower():
            css_content += line.strip() + "\n"

    if css_content.strip():
        errors.append({
            "type": "Phát hiện mã CSS",
            "message": "Đã phát hiện mã CSS trong thẻ <style>.",
            "line": "N/A",
            "highlight_line": None,
            "suggestion": "CSS đã được trích xuất để hiển thị riêng, kiểm tra và chỉnh sửa nếu cần.",
            "language": "CSS"
        })

    try:
        # Kiểm tra lỗi thẻ và thuộc tính với mã gốc
        errors.extend(check_lxml(html_code, original_lines))

        soup = BeautifulSoup(fixed_code, "html.parser")
        for style_tag in soup.find_all("style"):
            style_tag.decompose()
        for tag in soup.find_all():
            if not tag.contents and tag.name not in self_closing_tags:
                tag.string = ""
        
        # Kiểm tra thẻ mở và đóng <html>
        html_open_found = False
        html_close_line = None
        for i, line in enumerate(lines, 1):
            if re.search(r'<\s*html\b', line, re.IGNORECASE):
                html_open_found = True
            if re.search(r'</\s*html\s*>', line, re.IGNORECASE):
                html_close_line = i

        if not html_open_found:
            if html_close_line:
                errors.append({
                    "type": "Thiếu thẻ <html>",
                    "message": "Mã HTML không chứa phần tử html.",
                    "line": html_close_line,
                    "highlight_line": html_close_line,
                    "suggestion": "Thêm dòng <html lang=\"vi\"> sau <!DOCTYPE html> để tạo cấu trúc hợp lệ.",
                    "language": "HTML"
                })
            else:
                errors.append({
                    "type": "Thiếu thẻ <html>",
                    "message": "Mã HTML không chứa phần tử html.",
                    "line": 1,
                    "highlight_line": 1,
                    "suggestion": "Thêm dòng <html lang=\"vi\"> sau <!DOCTYPE html> để bắt đầu tài liệu.",
                    "language": "HTML"
                })

        # Kiểm tra thẻ chưa đóng và thẻ đóng không có thẻ mở
        open_tags = []
        closing_tags_without_opening = []
        for i, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            open_matches = re.findall(r'<([a-zA-Z][a-zA-Z0-9\-]*)\b[^>]*>', line_lower)
            close_matches = re.findall(r'</([a-zA-Z][a-zA-Z0-9\-]*)>', line_lower)
            
            print(f"📌 DEBUG: Line {i}: open_matches={open_matches}, close_matches={close_matches}")
            
            for tag in open_matches:
                if tag in valid_html_tags and tag not in self_closing_tags:
                    open_tags.append({"tag": tag, "line": i})
            
            for tag in close_matches:
                if tag in valid_html_tags and tag not in self_closing_tags:
                    found = False
                    for open_tag in reversed(open_tags):
                        if open_tag["tag"] == tag:
                            open_tags.remove(open_tag)
                            found = True
                            break
                    if not found:
                        closing_tags_without_opening.append({"tag": tag, "line": i})

        for open_tag in open_tags:
            errors.append({
                "type": "Thẻ chưa đóng",
                "message": f"Bạn đã mở thẻ &lt;{open_tag['tag']}&gt; nhưng chưa đóng.",
                "line": open_tag["line"],
                "highlight_line": open_tag["line"],
                "suggestion": f"Thêm thẻ đóng  &lt;/{open_tag['tag']}&gt; để hoàn thiện cấu trúc.",
                "language": "HTML"
            })

        for close_tag in closing_tags_without_opening:
            errors.append({
                "type": "Thẻ đóng không có thẻ mở",
                "message": f"Thẻ </{close_tag['tag']}> không có thẻ mở tương ứng.",
                "line": close_tag["line"],
                "highlight_line": close_tag["line"],
                "suggestion": f"Thêm thẻ <{close_tag['tag']}> trước hoặc xóa </{close_tag['tag']}> để sửa lỗi.",
                "language": "HTML"
            })

        # Kiểm tra thuộc tính (viết hoa và trùng lặp) với regex
        for i, line in enumerate(lines, 1):
            tag_match = re.search(r'<([a-zA-Z][a-zA-Z0-9\-]*)([^>]*)>', line)
            if tag_match:
                tag_name = tag_match.group(1)
                attrs_str = tag_match.group(2)
                attr_matches = re.findall(r'\b([A-Za-z][A-Za-z0-9\-]*)\s*=\s*["\'][^"\']*["\']', attrs_str)
                seen_attrs = {}
                uppercase_attrs = []
                duplicate_attrs = []

                for attr in attr_matches:
                    if attr.isupper():
                        uppercase_attrs.append(attr)
                    if attr in seen_attrs:
                        duplicate_attrs.append(attr)
                    seen_attrs[attr] = True

                if uppercase_attrs:
                    errors.append({
                        "type": "Thuộc tính viết hoa",
                        "message": f"Bạn đã viết thuộc tính {' và '.join(uppercase_attrs)} bằng chữ in hoa trong thẻ <{tag_name}>.",
                        "line": i,
                        "highlight_line": i,
                        "suggestion": f"Chuyển thuộc tính {' và '.join(uppercase_attrs)} thành chữ thường để tuân thủ chuẩn.",
                        "language": "HTML"
                    })
                if duplicate_attrs:
                    errors.append({
                        "type": "Thuộc tính trùng lặp",
                        "message": f"Bạn đã sử dụng thuộc tính {' và '.join(duplicate_attrs)} nhiều lần trong thẻ <{tag_name}>.",
                        "line": i,
                        "highlight_line": i,
                        "suggestion": f"Xóa thuộc tính {' và '.join(duplicate_attrs)} trùng lặp để tránh xung đột.",
                        "language": "HTML"
                    })

        # Kiểm tra DOCTYPE
        doctype_pattern = r"^\s*<!DOCTYPE\s+html\s*>"
        doctype_found = False
        doctype_line = None
        doctype_present = False

        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            if re.match(r"^\s*<!DOCTYPE\s+", stripped_line, re.IGNORECASE):
                doctype_present = True
                if re.match(doctype_pattern, stripped_line, re.IGNORECASE):
                    doctype_found = True
                    doctype_line = i
                    break

        if not doctype_present:
            errors.append({
                "type": "Thiếu khai báo <!DOCTYPE>",
                "message": "Tài liệu không có khai báo <!DOCTYPE>, cần thêm để tuân thủ chuẩn HTML5.",
                "line": 1,
                "highlight_line": 1,
                "suggestion": "Thêm <!DOCTYPE> vào dòng đầu tiên của tài liệu.",
                "language": "HTML"
            })
            fixed_code = "<!DOCTYPE html>\n" + fixed_code.lstrip()
        elif not doctype_found:
            errors.append({
                "type": "Khai báo <!DOCTYPE> sai",
                "message": "Tài liệu khai báo <!DOCTYPE> chưa đúng chuẩn HTML5.",
                "line": doctype_line,
                "highlight_line": doctype_line,
                "suggestion": "Thay <!DOCTYPE> bằng <!DOCTYPE html> để đảm bảo tài liệu tuân theo chuẩn HTML5.",
                "language": "HTML"
            })
            lines[doctype_line - 1] = "<!DOCTYPE html>"
            fixed_code = "\n".join(lines).strip()
        elif doctype_line == 1 and not re.match(doctype_pattern, lines[0], re.IGNORECASE):
            errors.append({
                "type": "Lỗi khai báo <!DOCTYPE>",
                "message": "Khai báo <!DOCTYPE> không đúng.",
                "line": doctype_line,
                "highlight_line": doctype_line,
                "suggestion": "Sửa thành <!DOCTYPE html> để tuân thủ chuẩn HTML5.",
                "language": "HTML"
            })
            lines[0] = "<!DOCTYPE html>"
            fixed_code = "\n".join(lines).strip()
        elif doctype_line > 1:
            errors.append({
                "type": "Lỗi khai báo DOCTYPE",
                "message": "Khai báo <!DOCTYPE> không đúng vị trí.",
                "line": doctype_line,
                "highlight_line": doctype_line,
                "suggestion": "Di chuyển và sửa thành <!DOCTYPE html> ở dòng đầu tiên.",
                "language": "HTML"
            })
            lines[0] = "<!DOCTYPE html>"
            if doctype_line <= len(lines):
                lines[doctype_line - 1] = ""
            fixed_code = "\n".join(lines).strip()
        else:
            fixed_code = html_code.strip()

        # Kiểm tra các thẻ khác
        misplaced_tags = []
        body_found = False
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            if "<body>" in line_lower:
                body_found = True
            if "<h1" in line_lower and not body_found:
                misplaced_tags.append({"tag": "h1", "line": i})

        for misplaced in misplaced_tags:
            errors.append({
                "type": "Thẻ nằm sai vị trí",
                "message": f"Thẻ <{misplaced['tag']}> nằm ngoài <body>.",
                "line": misplaced['line'],
                "highlight_line": misplaced['line'],
                "suggestion": f"Đặt thẻ <{misplaced['tag']}> bên trong thẻ <body> để đúng cấu trúc.",
                "language": "HTML"
            })

        if not soup.head:
            head_line = 2
            body_line = None
            for i, line in enumerate(lines, 1):
                if re.search(r'<\s*body\b', line, re.IGNORECASE):
                    body_line = i
                    head_line = i - 1 if i > 1 else i
                    break
            if not body_line:
                head_line = len(lines) + 1 if lines else 2

            message = "Thiếu thẻ &lt;head&gt;"
            full_message = "Thiếu thẻ &lt;head&gt; để chứa meta và tiêu đề."
            suggestion = "Thêm &lt;head&gt; ngay sau &lt;html&gt; và trước &lt;body&gt;."
            print(f"📌 DEBUG: Message: {full_message}")
            print(f"📌 DEBUG: Suggestion: {suggestion}")

            errors.append({
                "type": message,
                "message": full_message,
                "line": head_line,
                "highlight_line": head_line,
                "suggestion": suggestion,
                "language": "HTML"
            })
            new_head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, new_head)
            else:
                new_html = soup.new_tag("html")
                new_html["lang"] = "vi"
                soup.append(new_html)
                new_html.insert(0, new_head)

        if soup.html and "lang" not in [attr.lower() for attr in soup.html.attrs]:
            html_line = 1
            for i, line in enumerate(lines, 1):
                if re.search(r'<\s*html\b', line, re.IGNORECASE):
                    html_line = i
                    break
            errors.append({
                "type": "Thiếu thuộc tính ngôn ngữ",
                "message": "Thẻ html thiếu thuộc tính lang để xác định ngôn ngữ.",
                "line": html_line,
                "highlight_line": html_line,
                "suggestion": "Thêm lang=\"vi\" vào thẻ html.",
                "language": "HTML"
            })
            if soup.html:
                soup.html["lang"] = "vi"

        if not soup.html:
            soup.append(soup.new_tag("html"))
            soup.html["lang"] = "vi"
        if not soup.find("meta", charset=True):
            meta = soup.new_tag("meta")
            meta["charset"] = "UTF-8"
            soup.head.insert(0, meta)
        if not soup.title:
            soup.head.append(soup.new_tag("title"))
        if not soup.body:
            soup.html.append(soup.new_tag("body"))

        for tag in soup.find_all(True):
            new_attrs = {}
            for attr, value in tag.attrs.items():
                new_attrs[attr.lower()] = value
            tag.attrs = new_attrs

        for tag in soup.find_all(True):
            if tag.name in valid_html_tags and tag.name not in self_closing_tags and not tag.contents:
                tag.append("")

        pretty_html = soup.prettify().strip()
        if not doctype_found:
            fixed_code = "<!DOCTYPE html>\n" + re.sub(r'\n\s*\n+', '\n', pretty_html).strip()
        else:
            fixed_code = re.sub(r'\n\s*\n+', '\n', pretty_html).strip()
            if re.match(r"^\s*<!DOCTYPE\s+", fixed_code, re.IGNORECASE):
                fixed_code = re.sub(r"^\s*<!DOCTYPE\s+", "<!DOCTYPE html>", fixed_code, 1, re.IGNORECASE)

        if "html" in [tag["tag"] for tag in open_tags] and "</html>" not in fixed_code.lower():
            fixed_code += "\n</html>"
        if "body" in [tag["tag"] for tag in open_tags] and "</body>" not in fixed_code.lower():
            fixed_code += "\n</body>\n</html>"
        if "head" in [tag["tag"] for tag in open_tags] and "</head>" not in fixed_code.lower():
            fixed_code = fixed_code.rstrip("</html>").rstrip("</body") + "\n</head>\n<body>\n</body>\n</html>"

        print("📌 DEBUG: Fixed code before W3C:\n", fixed_code)

    except Exception as e:
        errors.append({
            "type": "Lỗi phân tích",
            "message": f"Đã xảy ra lỗi khi đọc mã HTML: {e}.",
            "line": "N/A",
            "highlight_line": None,
            "suggestion": "Kiểm tra cú pháp HTML và đảm bảo cấu trúc hợp lệ.",
            "language": "HTML"
        })


    errors.extend(check_lxml(fixed_code, original_lines))

    seen = set()
    unique_errors = []
    for error in errors:
        key = (error["type"], error["message"], str(error["line"]), str(error.get("highlight_line", "")))
        if key not in seen:
            seen.add(key)
            unique_errors.append(error)

    for error in unique_errors:
        error["message"] = error["message"].replace("<html>", "html").replace("</html>", "html")

    print("📌 DEBUG: Final fixed code:\n", fixed_code)
    print("📌 DEBUG: CSS content extracted:\n", css_content)
    print("📌 DEBUG: Errors detected:", unique_errors)
    return {
        "status": "✅ HTML hợp lệ" if not unique_errors else "❌ HTML lỗi",
        "errors": unique_errors,
        "fixed_code": fixed_code,
        "css_content": css_content
    }

if __name__ == "__main__":
    test_html = """
    <!DOCTYPE>
    <html lang="vi">
    <head>
        <title>Trang web</title>
    </head>
    <body>
        <h1>Chào mừng</h1>
    </body>
    </html>
    """
    result = check_html(test_html)
    print("Trạng thái:", result["status"])
    print("Fixed code:\n", result["fixed_code"])
    for error in result["errors"]:
        print(f"Ngôn ngữ: {error['language']}, Loại lỗi: {error['type']}, Thông báo: {error['message']}, Dòng: {error['line']}, Gợi ý sửa: {error['suggestion']}")