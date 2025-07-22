function xuLyXetDuyet() {
  const tenDangNhapInput = document.getElementById("tenDangNhapXetDuyet");
  const tenDangNhap = tenDangNhapInput.value;
  const loiXetDuyet = document.getElementById("loiXetDuyet");
  const thongBaoNoiDung = document.getElementById("thongBaoNoiDung");

  if (!tenDangNhap) {
    loiXetDuyet.textContent = "Vui lòng nhập tên đăng nhập!";
    loiXetDuyet.classList.remove("hidden");
    return;
  }

  const giangVienPattern = /^[A-Za-z]+@st\.tvu\.edu\.vn$/;
  if (!giangVienPattern.test(tenDangNhap)) {
    loiXetDuyet.textContent =
      "Email phải có định dạng của giảng viên (HueNguyet@st.tvu.edu.vn)!";
    loiXetDuyet.classList.remove("hidden");
    return;
  }

  loiXetDuyet.classList.add("hidden");

  fetch("http://127.0.0.1:8000/check_token", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Vui lòng đăng nhập lại!");
      return response.json();
    })
    .then((data) => {
      if (data.vai_tro !== "QuanTri") {
        throw new Error("Chỉ Quản trị mới có quyền xét duyệt!");
      }
      return fetch("http://127.0.0.1:8000/promote_to_giangvien/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
        body: JSON.stringify({ ten_dang_nhap: tenDangNhap }),
      });
    })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          throw new Error(data.detail || "Xét duyệt thất bại");
        });
      }
      return response.json();
    })
    .then((data) => {
      const modalXetDuyet = document.getElementById("modalXetDuyet");
      modalXetDuyet.style.display = "none";
      modalXetDuyet.classList.add("hidden");
      showNotification(data.message);
      tenDangNhapInput.value = "";
    })
    .catch((error) => {
      loiXetDuyet.textContent = error.message;
      loiXetDuyet.classList.remove("hidden");
    });
}

document.addEventListener("DOMContentLoaded", function () {
  const promoteTeacherButton = document.getElementById("promoteTeacherButton");
  if (promoteTeacherButton) {
    promoteTeacherButton.addEventListener("click", function () {
      window.location.href = "/xetduyet";
    });
  } else {
    console.warn("Không tìm thấy nút xét duyệt với id='promoteTeacherButton'");
  }
});

function showNotification(message) {
  const modalThongBao = document.getElementById("modalThongBao");
  const thongBaoNoiDung = document.getElementById("thongBaoNoiDung");
  thongBaoNoiDung.textContent = message;
  modalThongBao.style.display = "flex";
  modalThongBao.classList.remove("hidden");
  setTimeout(() => {
    modalThongBao.style.display = "none";
    modalThongBao.classList.add("hidden");
  }, 2000);
}
