document.addEventListener("DOMContentLoaded", () => {
  const tenDangNhapDangKy = document.getElementById("tenDangNhapDangKy");
  const sendVerificationCodeButton = document.getElementById(
    "sendVerificationCodeButton"
  );

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  tenDangNhapDangKy.addEventListener("input", (e) => {
    const email = e.target.value;
    const isValid = emailRegex.test(email);
    sendVerificationCodeButton.disabled = !isValid;
  });

  sendVerificationCodeButton.addEventListener("click", () => {
    const email = tenDangNhapDangKy.value;
    const loiDangKy = document.getElementById("loiDangKy");

    fetch("http://127.0.0.1:8000/send_verification_code", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(err.detail || "Gửi mã xác nhận thất bại");
          });
        }
        return response.json();
      })
      .then((data) => {
        loiDangKy.textContent = data.message;
        loiDangKy.classList.remove("text-red-600");
        loiDangKy.classList.add("text-green-600");
        loiDangKy.classList.remove("hidden");
      })
      .catch((error) => {
        loiDangKy.textContent = error.message;
        loiDangKy.classList.remove("text-green-600");
        loiDangKy.classList.add("text-red-600");
        loiDangKy.classList.remove("hidden");
      });
  });
});

function xuLyDangKy() {
  const tenDangNhap = document.getElementById("tenDangNhapDangKy").value;
  const matKhau = document.getElementById("matKhauDangKy").value;
  const maXacNhan = document.getElementById("maXacNhanDangKy").value;
  const isTeacherRole = document.getElementById("isTeacherRole").checked;
  const loiDangKy = document.getElementById("loiDangKy");
  const registerSuccess = document.getElementById("registerSuccess");
  const registerFormContent = document.getElementById("registerFormContent");

  if (!tenDangNhap || !matKhau || !maXacNhan) {
    loiDangKy.textContent = "Vui lòng điền đầy đủ thông tin!";
    loiDangKy.classList.remove("text-green-600");
    loiDangKy.classList.add("text-red-600");
    loiDangKy.classList.remove("hidden");
    return;
  }

  fetch("http://127.0.0.1:8000/dangky", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ten_dang_nhap: tenDangNhap,
      mat_khau: matKhau,
      ma_xac_nhan: maXacNhan,
      vai_tro: isTeacherRole ? "GiangVien" : "SinhVien",
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((err) => {
          throw new Error(err.detail || "Đăng ký thất bại");
        });
      }
      return response.json();
    })
    .then((data) => {
      registerFormContent.classList.add("hidden");
      registerSuccess.classList.remove("hidden");

      setTimeout(() => {
        document.getElementById("modalDangKy").classList.add("hidden");
        document.getElementById("modalDangNhap").classList.remove("hidden");

        registerSuccess.classList.add("hidden");
        registerFormContent.classList.remove("hidden");
        document.getElementById("tenDangNhapDangKy").value = "";
        document.getElementById("matKhauDangKy").value = "";
        document.getElementById("maXacNhanDangKy").value = "";
        document.getElementById("isTeacherRole").checked = false;
        loiDangKy.classList.add("hidden");
      }, 5000);
    })
    .catch((error) => {
      loiDangKy.textContent = error.message;
      loiDangKy.classList.remove("text-green-600");
      loiDangKy.classList.add("text-red-600");
      loiDangKy.classList.remove("hidden");
    });
}

function chuyenSangDangNhap() {
  document.getElementById("modalDangKy").classList.add("hidden");
  document.getElementById("modalDangNhap").classList.remove("hidden");
}
