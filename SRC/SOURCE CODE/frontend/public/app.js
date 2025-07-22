let isLoggedIn = false;
let editors = [];
let monacoInitialized = false;

// Đóng modal bằng phím Escape
document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    const modals = [
      "modalDangNhap",
      "modalDangKy",
      "modalThongBao",
      "detailModal",
      "historyModal",
    ];
    modals.forEach((modalId) => {
      const modal = document.getElementById(modalId);
      if (modal && !modal.classList.contains("hidden")) {
        modal.classList.add("hidden");
        modal.style.display = "none";
        console.log(`Modal ${modalId} đóng bằng phím Escape`);
      }
    });
  }
});

// Hàm mở trang chỉnh sửa thông tin
function openEditProfile(event) {
  event.preventDefault();
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để chỉnh sửa thông tin!");
    toggleModal("modalDangNhap", true);
    return;
  }
  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Token không hợp lệ");
      return response.json();
    })
    .then((data) => {
      if (
        data.vai_tro === "QuanTri" ||
        data.vai_tro === "GiangVien" ||
        data.vai_tro === "SinhVien"
      ) {
        window.location.href = "/chinhsuathongtin";
      } else {
        showNotification("Bạn không có quyền chỉnh sửa thông tin!");
      }
    })
    .catch((error) => {
      console.error("Lỗi kiểm tra token:", error);
      showNotification("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại!");
      localStorage.removeItem("access_token");
      checkLoginStatus();
    });
}

// Hàm chuyển hướng đến trang ttGV.html
function navigateToTeacherInfo(event) {
  event.preventDefault();
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để xem thông tin giảng viên!");
    toggleModal("modalDangNhap", true);
    return;
  }
  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Token không hợp lệ");
      return response.json();
    })
    .then((data) => {
      if (data.vai_tro === "QuanTri" || data.vai_tro === "GiangVien") {
        window.location.href = "/ttGV.html";
      } else {
        showNotification("Bạn không có quyền xem thông tin giảng viên!");
      }
    })
    .catch((error) => {
      console.error("Error checking token:", error);
      showNotification("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại!");
      localStorage.removeItem("access_token");
      checkLoginStatus();
    });
}

// Hàm chuyển hướng đến trang taobaitap.html
function navigateToCreateExercise(event) {
  event.preventDefault();
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để tạo bài tập!");
    toggleModal("modalDangNhap", true);
    return;
  }
  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Token không hợp lệ");
      return response.json();
    })
    .then((data) => {
      if (data.vai_tro === "GiangVien" || data.vai_tro === "QuanTri") {
        window.location.href = "/taobaitap.html";
      } else {
        showNotification("Bạn không có quyền tạo bài tập!");
      }
    })
    .catch((error) => {
      console.error("Error checking token:", error);
      showNotification("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại!");
      localStorage.removeItem("access_token");
      checkLoginStatus();
    });
}

// Hàm chuyển hướng đến trang tạo lớp học
function navigateToCreateClass(event) {
  event.preventDefault();
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để tạo lớp học!");
    toggleModal("modalDangNhap", true);
    return;
  }
  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(
          "Phiên đăng nhập không hợp lệ, vui lòng đăng nhập lại!"
        );
      return response.json();
    })
    .then((data) => {
      if (data.vai_tro === "GiangVien" || data.vai_tro === "QuanTri") {
        window.location.href = "/taolophoc";
      } else {
        showNotification("Bạn không có quyền tạo lớp học!");
      }
    })
    .catch((error) => {
      console.error("Error checking token:", error);
      showNotification(error.message);
      localStorage.removeItem("access_token");
      checkLoginStatus();
    });
}

// Hàm chuyển hướng đến danh sách lớp
function navigateToClassList(event) {
  event.preventDefault();
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để xem danh sách lớp!");
    toggleModal("modalDangNhap", true);
    return;
  }
  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Token không hợp lệ");
      return response.json();
    })
    .then((data) => {
      if (data.vai_tro === "GiangVien" || data.vai_tro === "QuanTri") {
        window.location.href = "/danhsachlop";
      } else {
        showNotification("Bạn không có quyền xem danh sách lớp!");
      }
    })
    .catch((error) => {
      console.error("Error checking token:", error);
      showNotification("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại!");
      localStorage.removeItem("access_token");
      checkLoginStatus();
    });
}

// Hàm kiểm tra trạng thái đăng nhập
function checkLoginStatus() {
  const token = localStorage.getItem("access_token");
  const loginButton = document.getElementById("loginButton");
  const logoutButton = document.getElementById("logoutButton");
  const userName = document.getElementById("userName");
  const userEmail = document.getElementById("userEmail");
  const userRole = document.getElementById("userRole");
  const userRoleHeader = document.getElementById("userRoleHeader");
  const checkButton = document.getElementById("checkButton");
  const historyButton = document.getElementById("historyButton");
  const viewStatsSidebar = document.getElementById("viewStatsSidebar");
  const viewInfoSidebar = document.getElementById("viewInfoSidebar");
  const createExerciseSidebar = document.getElementById(
    "createExerciseSidebar"
  );
  const manageExerciseSidebar = document.getElementById(
    "manageExerciseSidebar"
  );
  const manageClassSidebar = document.getElementById("manageClassSidebar");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.getElementById("mainContent");
  const userAvatar = document.getElementById("userAvatar");
  const editProfileLink = document.querySelector(".edit-icon");
  const teacherInfoLink = document.querySelector(
    '#infoSubButtons a[href="/thongtin/giangvien"]'
  );

  if (
    !loginButton ||
    !logoutButton ||
    !userName ||
    !userEmail ||
    !userRole ||
    !userRoleHeader ||
    !viewStatsSidebar ||
    !viewInfoSidebar ||
    !createExerciseSidebar ||
    !manageExerciseSidebar ||
    !manageClassSidebar ||
    !checkButton ||
    !historyButton ||
    !sidebar ||
    !mainContent ||
    !userAvatar ||
    !editProfileLink ||
    !teacherInfoLink
  ) {
    console.error(
      "Không tìm thấy một hoặc nhiều phần tử: loginButton, logoutButton, userName, userEmail, userRole, userRoleHeader, viewStatsSidebar, viewInfoSidebar, createExerciseSidebar, manageExerciseSidebar, manageClassSidebar, checkButton, historyButton, sidebar, mainContent, userAvatar, editProfileLink, teacherInfoLink"
    );
    return;
  }

  if (!token) {
    isLoggedIn = false;
    loginButton.classList.remove("hidden");
    logoutButton.classList.add("hidden");
    userName.textContent = "Tên người dùng";
    userEmail.textContent = "email@example.com";
    userRole.textContent = "Vai trò: Chưa xác định";
    userRoleHeader.classList.add("hidden");
    checkButton.disabled = true;
    historyButton.disabled = true;
    viewStatsSidebar.classList.add("hidden");
    viewInfoSidebar.classList.add("hidden");
    createExerciseSidebar.classList.add("hidden");
    manageExerciseSidebar.classList.add("hidden");
    manageClassSidebar.classList.add("hidden");
    sidebar.classList.add("hidden");
    mainContent.classList.remove("ml-[320px]");
    mainContent.classList.add("ml-0");
    userAvatar.src = "https://via.placeholder.com/50";
    return;
  }

  fetch(`http://127.0.0.1:8000/check_token/?_=${Date.now()}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Token không hợp lệ hoặc hết hạn");
        } else {
          throw new Error(
            `Lỗi server: ${response.status} - ${response.statusText}`
          );
        }
      }
      return response.json();
    })
    .then((data) => {
      console.log("Dữ liệu từ API /check_token:", data);
      isLoggedIn = true;
      loginButton.classList.add("hidden");
      logoutButton.classList.remove("hidden");

      const displayName =
        data.display_name && data.display_name.trim() !== ""
          ? data.display_name
          : data.ten_dang_nhap || "Tên người dùng";
      console.log("Tên hiển thị được chọn:", displayName);

      userName.textContent = displayName;
      userEmail.textContent = data.ten_dang_nhap || "email@example.com";
      userRole.textContent = `Vai trò: ${data.vai_tro}`;
      userRoleHeader.textContent = `Vai trò: ${data.vai_tro}`;
      userRoleHeader.classList.remove("hidden");
      checkButton.disabled = false;
      historyButton.disabled = false;

      userAvatar.src =
        data.avatar ||
        `https://via.placeholder.com/50?text=${encodeURIComponent(
          data.ten_dang_nhap || "User"
        )}`;

      localStorage.setItem("display_name", displayName);
      localStorage.setItem(
        "userAvatar",
        data.avatar || `https://via.placeholder.com/50`
      );
      localStorage.setItem("ten_dang_nhap", data.ten_dang_nhap);
      localStorage.setItem("vai_tro", data.vai_tro);

      if (
        data.vai_tro === "QuanTri" ||
        data.vai_tro === "GiangVien" ||
        data.vai_tro === "SinhVien"
      ) {
        sidebar.classList.remove("hidden");
        mainContent.classList.remove("ml-0");
        mainContent.classList.add("ml-[320px]");
      } else {
        sidebar.classList.add("hidden");
        mainContent.classList.remove("ml-[320px]");
        mainContent.classList.add("ml-0");
      }

      viewStatsSidebar.classList.add("hidden");
      viewInfoSidebar.classList.add("hidden");
      createExerciseSidebar.classList.add("hidden");
      manageExerciseSidebar.classList.add("hidden");
      manageClassSidebar.classList.add("hidden");

      if (data.vai_tro === "QuanTri") {
        viewStatsSidebar.classList.remove("hidden");
        viewInfoSidebar.classList.remove("hidden");
        // Ẩn hoàn toàn "Quản lý bài tập" và "Quản lý lớp" cho QuanTri
        manageExerciseSidebar.classList.add("hidden");
        document.getElementById("exerciseSubButtons").classList.add("hidden");
        manageClassSidebar.classList.add("hidden");
        document.getElementById("classSubButtons").classList.add("hidden");
      } else if (data.vai_tro === "GiangVien") {
        viewStatsSidebar.classList.remove("hidden");
        viewInfoSidebar.classList.remove("hidden");
        createExerciseSidebar.classList.remove("hidden");
        manageExerciseSidebar.classList.remove("hidden");
        manageClassSidebar.classList.remove("hidden");
      } else if (data.vai_tro === "SinhVien") {
        // Không hiển thị manageClassSidebar và manageExerciseSidebar
      }

      viewStatsSidebar.onclick = function (e) {
        e.preventDefault();
        if (data.vai_tro === "QuanTri" || data.vai_tro === "GiangVien") {
          window.location.href = "/thongke";
        } else {
          showNotification("Bạn không có quyền xem thống kê!");
        }
      };

      viewInfoSidebar.onclick = function (e) {
        e.preventDefault();
        toggleInfoSubButtons();
      };

      createExerciseSidebar.onclick = navigateToCreateExercise;

      manageExerciseSidebar.onclick = function (e) {
        e.preventDefault();
        const vaiTro = localStorage.getItem("vai_tro");
        if (vaiTro === "GiangVien") {
          toggleExerciseSubButtons();
        } else {
          showNotification("Bạn không có quyền quản lý bài tập!");
        }
      };

      manageClassSidebar.onclick = function (e) {
        e.preventDefault();
        const vaiTro = localStorage.getItem("vai_tro");
        if (vaiTro === "GiangVien") {
          toggleClassSubButtons();
        } else {
          showNotification("Bạn không có quyền quản lý lớp!");
        }
      };

      editProfileLink.onclick = openEditProfile;

      teacherInfoLink.onclick = navigateToTeacherInfo;

      const createClassLink = document.querySelector(
        '#classSubButtons a[href="/taolophoc"]'
      );
      if (createClassLink) {
        createClassLink.onclick = navigateToCreateClass;
      }

      const classListLink = document.querySelector(
        '#classSubButtons a[href="/danhsachlop"]'
      );
      if (classListLink) {
        classListLink.onclick = navigateToClassList;
      }
    })
    .catch((error) => {
      console.error("Lỗi kiểm tra token:", error);
      localStorage.removeItem("access_token");
      isLoggedIn = false;
      loginButton.classList.remove("hidden");
      logoutButton.classList.add("hidden");
      userName.textContent = "Tên người dùng";
      userEmail.textContent = "email@example.com";
      userRole.textContent = "Vai trò: Chưa xác định";
      userRoleHeader.classList.add("hidden");
      checkButton.disabled = true;
      historyButton.disabled = true;
      viewStatsSidebar.classList.add("hidden");
      viewInfoSidebar.classList.add("hidden");
      createExerciseSidebar.classList.add("hidden");
      manageExerciseSidebar.classList.add("hidden");
      manageClassSidebar.classList.add("hidden");
      sidebar.classList.add("hidden");
      mainContent.classList.remove("ml-[320px]");
      mainContent.classList.add("ml-0");
      userAvatar.src = "https://via.placeholder.com/50";
      showNotification(`Lỗi đăng nhập: ${error.message}. Vui lòng thử lại!`);
      toggleModal("modalDangNhap", true);
    });
}

// Đăng nhập
function login() {
  const tenDangNhap = document.getElementById("tenDangNhap").value;
  const matKhau = document.getElementById("matKhau").value;
  const loiDangNhap = document.getElementById("loiDangNhap");
  if (!tenDangNhap || !matKhau) {
    loiDangNhap.textContent = "Vui lòng nhập email và mật khẩu!";
    loiDangNhap.classList.remove("hidden");
    return;
  }

  fetch("http://127.0.0.1:8000/dangnhap", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      username: tenDangNhap,
      password: matKhau,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((err) => {
          throw new Error(err.detail || "Đăng nhập thất bại");
        });
      }
      return response.json();
    })
    .then((data) => {
      localStorage.setItem("access_token", data.access_token);
      toggleModal("modalDangNhap", false);
      checkLoginStatus();
    })
    .catch((error) => {
      console.error("Lỗi đăng nhập:", error);
      loiDangNhap.textContent = `Đăng nhập thất bại: ${error.message}`;
      loiDangNhap.classList.remove("hidden");
    });
}

// Khởi tạo Monaco Editor
function initializeMonaco() {
  if (monacoInitialized) return;
  require.config({
    paths: {
      vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0/min/vs",
    },
  });
  require(["vs/editor/editor.main"], function () {
    monacoInitialized = true;
    createEditorsForExistingSets();
    console.log("Monaco Editor initialized successfully");
  });
}

// Tạo editor cho các set mã hiện có
function createEditorsForExistingSets() {
  const codeSets = document.querySelectorAll(".code-set");
  codeSets.forEach((set, setIndex) => {
    const htmlEditorDiv = set.querySelector(".html-editor");
    const cssEditorDiv = set.querySelector(".css-editor");
    const jsEditorDiv = set.querySelector(".js-editor");

    if (htmlEditorDiv && cssEditorDiv && jsEditorDiv && monacoInitialized) {
      editors[setIndex] = {
        html: monaco.editor.create(htmlEditorDiv, {
          value: "",
          language: "html",
          theme: "vs-dark",
          automaticLayout: true,
          minimap: { enabled: false },
        }),
        css: monaco.editor.create(cssEditorDiv, {
          value: "",
          language: "css",
          theme: "vs-dark",
          automaticLayout: true,
          minimap: { enabled: false },
        }),
        js: monaco.editor.create(jsEditorDiv, {
          value: "",
          language: "javascript",
          theme: "vs-dark",
          automaticLayout: true,
          minimap: { enabled: false },
        }),
      };
      console.log(`Created editors for set ${setIndex + 1}`);
    } else {
      console.error(`Failed to initialize editors for set ${setIndex + 1}`);
    }
  });
}

// Tạo editor cho set mã mới
function createEditorForNewSet(setIndex, setElement) {
  const htmlEditorDiv = setElement.querySelector(".html-editor");
  const cssEditorDiv = setElement.querySelector(".css-editor");
  const jsEditorDiv = setElement.querySelector(".js-editor");

  if (htmlEditorDiv && cssEditorDiv && jsEditorDiv && monacoInitialized) {
    editors[setIndex] = {
      html: monaco.editor.create(htmlEditorDiv, {
        value: "",
        language: "html",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
      }),
      css: monaco.editor.create(cssEditorDiv, {
        value: "",
        language: "css",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
      }),
      js: monaco.editor.create(jsEditorDiv, {
        value: "",
        language: "javascript",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
      }),
    };
    console.log(`Created new editors for set ${setIndex + 1}`);
  } else {
    console.error(`Failed to initialize new editors for set ${setIndex + 1}`);
  }
}

// Đăng xuất
function logout() {
  localStorage.removeItem("access_token");
  isLoggedIn = false;
  checkLoginStatus();
}

// Đóng thông báo
function dongThongBao() {
  toggleModal("modalThongBao", false);
}

// Chuyển sang đăng ký
function chuyenSangDangKy() {
  toggleModal("modalDangNhap", false);
  toggleModal("modalDangKy", true);
}

// Chuyển sang đăng nhập
function chuyenSangDangNhap() {
  toggleModal("modalDangKy", false);
  toggleModal("modalDangNhap", true);
}

// Hiển thị thông báo
function showNotification(message) {
  const modalThongBao = document.getElementById("modalThongBao");
  const thongBaoNoiDung = document.getElementById("thongBaoNoiDung");
  if (modalThongBao && thongBaoNoiDung) {
    thongBaoNoiDung.textContent = message;
    modalThongBao.style.display = "flex";
    modalThongBao.classList.remove("hidden");
    setTimeout(() => {
      modalThongBao.style.display = "none";
      modalThongBao.classList.add("hidden");
    }, 2000);
  }
}

// Thêm bộ mã mới
function addCodeSet() {
  const codeSetsContainer = document.getElementById("codeSets");
  const setCount = codeSetsContainer.children.length + 1;
  const setIndex = setCount - 1;

  const newSet = document.createElement("div");
  newSet.className = "code-set bg-gray-50 p-4 rounded-lg";
  newSet.innerHTML = `
    <h3 class="text-lg font-semibold text-gray-800 mb-2">Bộ mã ${setCount}</h3>
    <div class="flex flex-wrap gap-6 mb-4">
      <label class="flex items-center space-x-2">
        <input type="checkbox" name="language-${setIndex}" value="HTML" class="html-checkbox h-5 w-5 text-blue-600 rounded" checked />
        <span class="text-gray-700 font-medium">HTML</span>
      </label>
      <label class="flex items-center space-x-2">
        <input type="checkbox" name="language-${setIndex}" value="CSS" class="css-checkbox h-5 w-5 text-blue-600 rounded" />
        <span class="text-gray-700 font-medium">CSS</span>
      </label>
      <label class="flex items-center space-x-2">
        <input type="checkbox" name="language-${setIndex}" value="JavaScript" class="js-checkbox h-5 w-5 text-blue-600 rounded" />
        <span class="text-gray-700 font-medium">JavaScript</span>
      </label>
    </div>
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Mã HTML:</label>
        <div class="html-editor editor-container" data-editor-type="html"></div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Mã CSS:</label>
        <div class="css-editor editor-container" data-editor-type="css"></div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Mã JavaScript:</label>
        <div class="js-editor editor-container" data-editor-type="javascript"></div>
      </div>
    </div>
  `;
  codeSetsContainer.appendChild(newSet);

  if (monacoInitialized) {
    createEditorForNewSet(setIndex, newSet);
  } else {
    initializeMonaco();
    setTimeout(() => createEditorForNewSet(setIndex, newSet), 100);
  }
}

// Tách mã nguồn
function splitCode(content) {
  let html = content;
  let css = "";
  let js = "";

  const styleMatch = content.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
  if (styleMatch) {
    css = styleMatch[1].trim();
    html = html.replace(styleMatch[0], "").trim();
  }

  const scriptMatch = content.match(/<script[^>]*>([\s\S]*?)<\/script>/i);
  if (scriptMatch) {
    js = scriptMatch[1].trim();
    let openBraces = (js.match(/{/g) || []).length;
    let closeBraces = (js.match(/}/g) || []).length;
    if (openBraces > closeBraces && js.includes("function")) {
      console.warn("Lỗi cú pháp: Thiếu dấu } trong JavaScript tại editor JS");
    }
    html = html.replace(scriptMatch[0], "").trim();
  }

  return { html, css, js };
}

// Kiểm tra mã
function checkCode() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    showNotification("Vui lòng đăng nhập để kiểm tra mã!");
    toggleModal("modalDangNhap", true);
    return;
  }

  fetch("http://127.0.0.1:8000/check_token", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Token không hợp lệ");
      return response.json();
    })
    .then(() => {
      const codeSets = document.querySelectorAll(".code-set");
      const codes = [];

      let hasCode = false;
      let hasLanguage = false;

      codeSets.forEach((set, index) => {
        const htmlCode = editors[index]?.html?.getValue().trim() || "";
        const cssCode = editors[index]?.css?.getValue().trim() || "";
        const jsCode = editors[index]?.js?.getValue().trim() || "";
        const languages = Array.from(
          set.querySelectorAll(`input[name="language-${index}"]:checked`)
        ).map((checkbox) => checkbox.value);

        if (htmlCode || cssCode || jsCode) hasCode = true;
        if (languages.length > 0) hasLanguage = true;

        if (htmlCode && !cssCode && !jsCode && languages.includes("HTML")) {
          const { html, css, js } = splitCode(htmlCode);
          codes.push({ html, css, js, languages });
          if (editors[index]) {
            editors[index].html.setValue(html);
            if (css) editors[index].css.setValue(css);
            if (js) editors[index].js.setValue(js);
          }
        } else {
          codes.push({ html: htmlCode, css: cssCode, js: jsCode, languages });
        }
      });

      if (!hasCode) {
        showNotification("Vui lòng nhập ít nhất một đoạn mã để kiểm tra!");
        return;
      }

      if (!hasLanguage) {
        showNotification("Vui lòng chọn ít nhất một ngôn ngữ để kiểm tra!");
        return;
      }

      document.getElementById("loading").classList.remove("hidden");
      document.getElementById("statusBar").textContent = "Đang kiểm tra...";

      fetch("http://127.0.0.1:8000/check_code/", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ codes }),
      })
        .then((response) => {
          document.getElementById("loading").classList.add("hidden");
          if (!response.ok) {
            return response.json().then((err) => {
              throw new Error(err.detail || "Lỗi khi kiểm tra mã");
            });
          }
          return response.json();
        })
        .then((results) => {
          console.log("Dữ liệu từ API /check_code:", results);
          updateSuggestionTable(results);

          results.forEach((result, idx) => {
            const codeSet = codeSets[idx];
            const htmlCheckbox = codeSet.querySelector(".html-checkbox");
            const cssCheckbox = codeSet.querySelector(".css-checkbox");
            const jsCheckbox = codeSet.querySelector(".js-checkbox");

            htmlCheckbox.checked = false;
            cssCheckbox.checked = false;
            jsCheckbox.checked = false;

            result.detected_languages.forEach((lang) => {
              if (lang === "HTML") htmlCheckbox.checked = true;
              if (lang === "CSS") cssCheckbox.checked = true;
              if (lang === "JavaScript") jsCheckbox.checked = true;
            });
          });

          const allValid = results.every(
            (result) => result.errors.length === 0
          );
          document.getElementById("statusBar").textContent = allValid
            ? "✅ Tất cả mã hợp lệ"
            : "❌ Có lỗi trong mã";
        })
        .catch((error) => {
          console.error("Chi tiết lỗi:", error);
          document.getElementById(
            "statusBar"
          ).textContent = `Lỗi: ${error.message}`;
          showNotification(`Không thể kiểm tra mã: ${error.message}`);
        });
    })
    .catch((error) => {
      console.error("Lỗi kiểm tra token:", error);
      localStorage.removeItem("access_token");
      isLoggedIn = false;
      checkLoginStatus();
      showNotification("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại!");
      toggleModal("modalDangNhap", true);
    });
}

// Cập nhật bảng gợi ý
function updateSuggestionTable(results) {
  const suggestionTableBody = document.getElementById("suggestionTableBody");
  const aiSuggestionTableBody = document.getElementById(
    "aiSuggestionTableBody"
  );
  suggestionTableBody.innerHTML = "";
  aiSuggestionTableBody.innerHTML = "";
  let hasErrors = false;
  let hasAiSuggestions = false;

  results.forEach((result, setIndex) => {
    if (result.errors && result.errors.length > 0) {
      hasErrors = true;
      result.errors.forEach((error) => {
        const row = document.createElement("tr");
        row.className = "errorHighlight";
        row.innerHTML = `
          <td class="border p-2">Bộ mã ${setIndex + 1}</td>
          <td class="border p-2">${error.language || "N/A"}</td>
          <td class="border p-2">${error.type || "Lỗi cú pháp"}</td>
          <td class="border p-2">${error.message}</td>
          <td class="border p-2">${error.line || "N/A"}</td>
          <td class="border p-2">${error.suggestion || "Không có gợi ý"}</td>
        `;
        suggestionTableBody.appendChild(row);
      });
    }

    if (result.ai_suggestions && result.ai_suggestions.length > 0) {
      hasAiSuggestions = true;
      result.ai_suggestions.forEach((suggestion) => {
        const row = document.createElement("tr");
        row.className = "aiHighlight";
        row.innerHTML = `
          <td class="border p-2">Bộ mã ${setIndex + 1}</td>
          <td class="border p-2">${suggestion.language || "N/A"}</td>
          <td class="border p-2">${suggestion.type || "Cải tiến"}</td>
          <td class="border p-2">${suggestion.info || "Không có gợi ý"}</td>
        `;
        aiSuggestionTableBody.appendChild(row);
      });
    }
  });

  const suggestionTable = document.getElementById("suggestionTable");
  const noSuggestions = document.getElementById("noSuggestions");
  if (hasErrors) {
    suggestionTable.classList.remove("hidden");
    noSuggestions.classList.add("hidden");
  } else {
    suggestionTable.classList.add("hidden");
    noSuggestions.classList.remove("hidden");
  }

  const aiSuggestionTable = document.getElementById("aiSuggestionTable");
  const noAiSuggestions = document.getElementById("noAiSuggestions");
  if (hasAiSuggestions) {
    aiSuggestionTable.classList.remove("hidden");
    noAiSuggestions.classList.add("hidden");
  } else {
    aiSuggestionTable.classList.add("hidden");
    noAiSuggestions.classList.remove("hidden");
  }
}

// Hiển thị chi tiết lỗi
function showDetails(errorJson) {
  const error = JSON.parse(errorJson);
  const modalContent = document.getElementById("modalContent");
  modalContent.textContent = JSON.stringify(error, null, 2);
  toggleModal("detailModal", true);
}

// Đóng modal chi tiết
function closeModal() {
  toggleModal("detailModal", false);
}

// Xử lý upload file
document.getElementById("uploadButton").addEventListener("click", function () {
  document.getElementById("uploadFile").click();
});

document
  .getElementById("uploadFile")
  .addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (file) {
      const fileExtension = file.name
        .slice(file.name.lastIndexOf(".") + 1)
        .toLowerCase();

      const codeSets = document.querySelectorAll(".code-set");
      let targetSetIndex = codeSets.length > 0 ? codeSets.length - 1 : 0;
      if (codeSets.length === 0) addCodeSet();

      const reader = new FileReader();
      reader.onload = function (e) {
        const content = e.target.result;
        const editor = editors[targetSetIndex];
        const { html, css, js } = splitCode(content);
        console.log("Mã JS sau khi tách:", js);

        if (editor) {
          editor.html.setValue(html);
          if (css) editor.css.setValue(css);
          if (js) editor.js.setValue(js || "");
        }

        if (
          js &&
          js.includes("function") &&
          (js.match(/{/g) || []).length > (js.match(/}/g) || []).length
        ) {
          showNotification(
            "Lỗi cú pháp: Thiếu dấu } trong JavaScript. Vui lòng sửa trước khi kiểm tra!"
          );
        }

        const checkboxes = document.querySelectorAll(
          `input[name="language-${targetSetIndex}"]`
        );
        checkboxes.forEach((checkbox) => {
          if (checkbox.value === "HTML") checkbox.checked = true;
          if (checkbox.value === "CSS" && css) checkbox.checked = true;
          if (checkbox.value === "JavaScript" && js) checkbox.checked = true;
        });
      };
      reader.readAsText(file);
      event.target.value = "";
    }
  });

// Hiển thị/ẩn các nút con của "Xem thông tin"
function toggleInfoSubButtons() {
  const subButtons = document.getElementById("infoSubButtons");
  if (subButtons.style.display === "block") {
    subButtons.style.display = "none";
  } else {
    subButtons.style.display = "block";
  }
}

// Hiển thị/ẩn các nút con của "Quản lý lớp"
function toggleClassSubButtons() {
  const subButtons = document.getElementById("classSubButtons");
  if (subButtons.style.display === "block") {
    subButtons.style.display = "none";
  } else {
    subButtons.style.display = "block";
  }
}

// Khởi tạo sự kiện khi DOM được tải
document.addEventListener("DOMContentLoaded", function () {
  const logoutButton = document.getElementById("logoutButton");
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  } else {
    console.error("Không tìm thấy nút đăng xuất với id='logoutButton'");
  }

  const checkButton = document.getElementById("checkButton");
  if (checkButton) {
    checkButton.addEventListener("click", checkCode);
  } else {
    console.error("Không tìm thấy nút kiểm tra mã với id='checkButton'");
  }

  const addCodeSetButton = document.getElementById("addCodeSetButton");
  if (addCodeSetButton) {
    addCodeSetButton.addEventListener("click", addCodeSet);
  }

  const loginButton = document.getElementById("loginButton");
  if (loginButton) {
    loginButton.addEventListener("click", function () {
      toggleModal("modalDangNhap", true);
    });
  }

  const loginSubmitButton = document.getElementById("loginSubmitButton");
  if (loginSubmitButton) {
    loginSubmitButton.addEventListener("click", login);
  }

  checkLoginStatus();
  initializeMonaco();

  window.addEventListener("storage", () => {
    checkLoginStatus();
  });
});
