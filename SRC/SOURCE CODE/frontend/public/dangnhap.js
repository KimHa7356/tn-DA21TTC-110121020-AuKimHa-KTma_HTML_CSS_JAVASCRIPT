document.addEventListener("DOMContentLoaded", function () {
  const loginSubmitButton = document.getElementById("loginSubmitButton");
  if (loginSubmitButton) {
    loginSubmitButton.addEventListener("click", function () {
      const tenDangNhap = document.getElementById("tenDangNhap").value;
      const matKhau = document.getElementById("matKhau").value;

      if (!tenDangNhap || !matKhau) {
        showNotification("Vui lòng nhập đầy đủ email và mật khẩu!");
        return;
      }

      fetch("http://127.0.0.1:8000/dangnhap", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: tenDangNhap,
          password: matKhau,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw new Error(err.detail || "Lỗi đăng nhập");
            });
          }
          return response.json();
        })
        .then((data) => {
          localStorage.setItem("access_token", data.access_token);
          document.getElementById("modalDangNhap").style.display = "none";
          document.getElementById("modalDangNhap").classList.add("hidden");
          showNotification("Đăng nhập thành công!");
          checkLoginStatus();
        })
        .catch((error) => {
          showNotification(`Đăng nhập thất bại: ${error.message}`);
        });
    });
  }
});
