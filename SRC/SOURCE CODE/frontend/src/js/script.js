let editor;

require.config({
  paths: {
    vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0/min/vs",
  },
});
//Kiểm tra đoạn code
function checkCode() {
  console.log("Nút kiểm tra đã được nhấn!");

  const selectedLanguages = [];
  const checkboxes = document.querySelectorAll(
    'input[name="language"]:checked'
  );

  checkboxes.forEach((checkbox) => {
    selectedLanguages.push(checkbox.value);
  });

  if (selectedLanguages.length === 0) {
    alert("Vui lòng chọn ít nhất một ngôn ngữ để kiểm tra!");
    return;
  }

  console.log("Ngôn ngữ đã chọn:", selectedLanguages);
}

// Hiển thị lịch sử kiểm tra từ API
fetch("http://127.0.0.1:8000/history/")
  .then((response) => response.json())
  .then((data) => {
    let historyTable = document.getElementById("historyTable");
    historyTable.innerHTML = ""; // Xóa nội dung cũ

    data.forEach((item) => {
      let row = `<tr>
          <td>${item.id}</td>
          <td>${item.timestamp}</td>
          <td>${item.languages.join(", ")}</td>
          <td>${JSON.stringify(item.result)}</td>
      </tr>`;
      historyTable.innerHTML += row;
    });
  })
  .catch((error) => console.error("Lỗi:", error));

// Hiển thị lịch sử từ LocalStorage
function displayHistory() {
  let history = JSON.parse(localStorage.getItem("checkHistory")) || [];
  let historyTable = document.querySelector("#historyTable tbody");

  historyTable.innerHTML = ""; // Xóa dữ liệu cũ

  history.forEach((entry) => {
    let row = `<tr>
            <td>${entry.id}</td>
            <td>${entry.time}</td>
            <td>${entry.languages.join(", ")}</td>
            <td><button onclick='viewDetail(${entry.id})'>Xem</button></td>
        </tr>`;
    historyTable.innerHTML += row;
  });
}

function viewDetail(id) {
  let history = JSON.parse(localStorage.getItem("checkHistory")) || [];
  let entry = history.find((e) => e.id === id);
  alert("Chi tiết kiểm tra:\n" + JSON.stringify(entry.result, null, 2));
}

document.addEventListener("DOMContentLoaded", displayHistory);

// Khởi tạo Monaco Editor cho HTML
require.config({
  paths: {
    vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0/min/vs",
  },
});
require(["vs/editor/editor.main"], function () {
  window.htmlEditor = monaco.editor.create(
    document.getElementById("htmlEditor"),
    {
      value: "",
      language: "html",
      theme: "vs-light",
    }
  );
});

// Xử lý sự kiện chọn ngôn ngữ
document.getElementById("htmlCheckbox").addEventListener("change", function () {
  document
    .getElementById("htmlEditor")
    .classList.toggle("hidden", !this.checked);
});

document.addEventListener("DOMContentLoaded", function () {
  // Hàm kiểm tra ngôn ngữ đã được chọn hay chưa
  function checkLanguageSelection() {
    const checkboxes = document.querySelectorAll('input[name="language"]');
    const codeLabel = document.getElementById("codeLabel");
    const checkButton = document.getElementById("checkButton");
    const codeInput = document.getElementById("codeInput");

    // Kiểm tra nếu chưa có ngôn ngữ nào được chọn
    const selectedLanguages = [];
    checkboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        selectedLanguages.push(checkbox.value);
      }
    });

    if (selectedLanguages.length === 0) {
      codeLabel.textContent = "Hãy chọn ít nhất 1 ngôn ngữ để kiểm tra";
      codeInput.disabled = true; // Khoá ô nhập mã nguồn
      checkButton.disabled = true; // Khoá nút kiểm tra
    } else {
      codeLabel.textContent = "Mã nguồn: " + selectedLanguages.join(" + ");
      codeInput.disabled = false; // Mở lại ô nhập mã nguồn
      checkButton.disabled = false; // Mở lại nút kiểm tra
    }
  }

  // Lắng nghe sự thay đổi checkbox và gọi hàm kiểm tra
  document.querySelectorAll('input[name="language"]').forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const selectedLanguages = [];
      const checkboxes = document.querySelectorAll(
        'input[name="language"]:checked'
      );

      checkboxes.forEach((checkbox) => {
        selectedLanguages.push(checkbox.value); // Lấy ngôn ngữ đã chọn
      });

      // Cập nhật tiêu đề "Mã nguồn:"
      if (selectedLanguages.length > 0) {
        document.getElementById("codeLabel").textContent =
          "Mã nguồn: " + selectedLanguages.join(" + ");
      } else {
        document.getElementById("codeLabel").textContent = "Mã nguồn:";
      }

      // Thay đổi ngôn ngữ cho Monaco Editor khi người dùng chọn
      const currentContent = editor.getValue();
      let newModel;
      if (selectedLanguages.includes("HTML")) {
        newModel = monaco.editor.createModel(currentContent, "html");
      } else if (selectedLanguages.includes("CSS")) {
        newModel = monaco.editor.createModel(currentContent, "css");
      } else if (selectedLanguages.includes("JavaScript")) {
        newModel = monaco.editor.createModel(currentContent, "javascript");
      }
      editor.setModel(newModel);
    });
  });

  // Lần đầu khi trang được tải, kiểm tra tình trạng ngôn ngữ
  checkLanguageSelection();
});
const css_code = document.getElementById("cssInput").value; // Giả sử có input chứa CSS
console.log(css_code); // In ra dữ liệu CSS
// Hiển thị các lỗi kiểm tra CSS lên giao diện
function displayErrors(errors) {
  const errorContainer = document.getElementById("errorContainer");
  errorContainer.innerHTML = ""; // Xóa các lỗi cũ

  errors.forEach((error) => {
    const errorElement = document.createElement("div");
    errorElement.classList.add("error");
    errorElement.textContent = `${error.type}: ${error.message}`;
    errorContainer.appendChild(errorElement);
  });
}

function checkCSSCode() {
  const cssCode = editor.getValue(); // Lấy mã CSS từ Monaco Editor

  // Gửi mã CSS lên backend để kiểm tra
  fetch("http://127.0.0.1:8000/check_css/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ css_code: cssCode }), // Gửi mã CSS
  })
    .then((response) => response.json())
    .then((data) => {
      displayErrors(data.errors); // Hiển thị lỗi lên giao diện
    })
    .catch((error) => {
      console.error("Lỗi kết nối với backend:", error);
    });
}
