function displayHistory(history, filter = "") {
  const historyTableBody = document.getElementById("historyTableBody");
  const noHistoryDiv = document.getElementById("noHistory");
  historyTableBody.innerHTML = "";

  const filteredHistory = filter
    ? history.filter(
        (entry) =>
          entry.languages.some((lang) =>
            lang.toLowerCase().includes(filter.toLowerCase())
          ) || entry.ten_dang_nhap.toLowerCase().includes(filter.toLowerCase())
      )
    : history;

  if (filteredHistory.length === 0) {
    noHistoryDiv.classList.remove("hidden");
    return;
  }

  noHistoryDiv.classList.add("hidden");
  filteredHistory.forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
        <td>${entry.id}</td>
        <td>${entry.timestamp}</td>
        <td>${entry.languages.join(", ")}</td>
        <td>${entry.ten_dang_nhap}</td>
        <td>${
          entry.result.errors.length > 0
            ? `${entry.result.errors.length} lỗi`
            : "Hợp lệ"
        }</td>
        <td><button class="text-blue-600 hover:underline text-sm" onclick="viewDetail(${
          entry.id
        })">Xem chi tiết</button></td>
      `;
    historyTableBody.appendChild(row);
  });
}
function displayStats(stats) {
  const statsTableBody = document.getElementById("statsTableBody");
  const noStatsDiv = document.getElementById("noStats");
  statsTableBody.innerHTML = "";

  if (stats.length === 0) {
    noStatsDiv.classList.remove("hidden");
    return;
  }

  noStatsDiv.classList.add("hidden");
  stats.forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.ten_dang_nhap}</td>
      <td>${entry.login_count}</td>
      <td>${entry.code_check_count}</td>
    `;
    statsTableBody.appendChild(row);
  });
}

function fetchStats() {
  fetch("http://127.0.0.1:8000/user_stats/", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Không thể lấy thống kê");
      return response.json();
    })
    .then((data) => {
      console.log("Thống kê từ API:", data);
      displayStats(data);
    })
    .catch((error) => {
      console.error("Lỗi tải thống kê:", error);
      document.getElementById("noStats").classList.remove("hidden");
      document.getElementById("noStats").textContent =
        "Không thể tải thống kê.";
    });
}

// Cập nhật DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  checkLoginStatus();
  fetchHistory();
  fetchStats();
});
function fetchHistory() {
  const historyTableBody = document.getElementById("historyTableBody");
  const noHistoryDiv = document.getElementById("noHistory");
  historyTableBody.innerHTML =
    '<tr><td colspan="6" class="text-center text-blue-600 font-medium">Đang tải...</td></tr>';

  fetch("http://127.0.0.1:8000/history/", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          window.location.href = "/";
        }
        throw new Error("API history không phản hồi");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Lịch sử từ API:", data);
      localStorage.setItem("checkHistory", JSON.stringify(data));
      displayHistory(data);
    })
    .catch((error) => {
      console.error("Lỗi tải lịch sử:", error);
      historyTableBody.innerHTML = "";
      noHistoryDiv.classList.remove("hidden");
      noHistoryDiv.textContent = "Không thể tải lịch sử từ server.";
    });
}

window.viewDetail = function (id) {
  let history = JSON.parse(localStorage.getItem("checkHistory") || "[]");
  let entry = history.find((e) => e.id === id);
  if (entry) {
    const modal = document.getElementById("detailModal");
    const modalContent = document.getElementById("modalContent");
    modalContent.textContent = JSON.stringify(entry.result, null, 2);
    modal.classList.add("active");
  }
};

window.closeModal = function () {
  document.getElementById("detailModal").classList.remove("active");
};

function checkLoginStatus() {
  const token = localStorage.getItem("access_token");
  const userRoleSpan = document.getElementById("userRole");
  if (token) {
    fetch("http://127.0.0.1:8000/check_token", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        if (!response.ok) throw new Error("Token không hợp lệ");
        return response.json();
      })
      .then((data) => {
        userRoleSpan.textContent = `Vai trò: ${data.vai_tro}`;
        userRoleSpan.classList.remove("hidden");
      })
      .catch((error) => {
        console.error("Lỗi kiểm tra token:", error);
        localStorage.removeItem("access_token");
        window.location.href = "/";
      });
  } else {
    window.location.href = "/";
  }
}

document.getElementById("historySearch").addEventListener("input", (e) => {
  let history = JSON.parse(localStorage.getItem("checkHistory") || "[]");
  displayHistory(history, e.target.value);
});

document
  .getElementById("refreshHistory")
  .addEventListener("click", fetchHistory);

document.addEventListener("DOMContentLoaded", () => {
  checkLoginStatus();
  fetchHistory();
});
