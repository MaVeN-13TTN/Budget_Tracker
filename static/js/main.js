document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on the index page
  if (document.getElementById("summary")) {
    fetchSummaryData();
    fetchRecentTransactions();
  }

  // Check if we're on the reports page
  if (document.getElementById("date-range")) {
    // Set default date range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    document.getElementById("start-date").valueAsDate = thirtyDaysAgo;
    document.getElementById("end-date").valueAsDate = today;

    document
      .getElementById("update-report")
      .addEventListener("click", updateReport);

    // Initial report load
    updateReport();
  }

  // Setup form validation
  setupFormValidation();
});

function fetchSummaryData() {
  fetch("/api/summary")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById(
        "total-income"
      ).textContent = `$${data.total_income.toFixed(2)}`;
      document.getElementById(
        "total-expenses"
      ).textContent = `$${data.total_expenses.toFixed(2)}`;
      document.getElementById("balance").textContent = `$${(
        data.total_income - data.total_expenses
      ).toFixed(2)}`;

      createExpenseChart(data.expense_categories);
    })
    .catch((error) => console.error("Error fetching summary data:", error));
}

function fetchRecentTransactions() {
  fetch("/api/recent_transactions")
    .then((response) => response.json())
    .then((data) => {
      const tbody = document.querySelector("#recent-transactions tbody");
      tbody.innerHTML = "";
      data.forEach((transaction) => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = new Date(
          transaction.date
        ).toLocaleDateString();
        row.insertCell(1).textContent = transaction.type;
        row.insertCell(2).textContent = `$${transaction.amount.toFixed(2)}`;
        row.insertCell(3).textContent = transaction.description;
      });
    })
    .catch((error) =>
      console.error("Error fetching recent transactions:", error)
    );
}

function createExpenseChart(categories) {
  const ctx = document.getElementById("expense-chart").getContext("2d");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: Object.keys(categories),
      datasets: [
        {
          data: Object.values(categories),
          backgroundColor: [
            "#FF6384",
            "#36A2EB",
            "#FFCE56",
            "#4BC0C0",
            "#9966FF",
            "#FF9F40",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      title: {
        display: true,
        text: "Expense Distribution",
      },
    },
  });
}

function updateReport() {
  const startDate = document.getElementById("start-date").value || "";
  const endDate = document.getElementById("end-date").value || "";

  fetch(`/api/report_data?start_date=${startDate}&end_date=${endDate}`)
    .then((response) => response.json())
    .then((data) => {
      document.getElementById(
        "report-total-income"
      ).textContent = `$${data.total_income.toFixed(2)}`;
      document.getElementById(
        "report-total-expenses"
      ).textContent = `$${data.total_expenses.toFixed(2)}`;
      document.getElementById(
        "report-net-income"
      ).textContent = `$${data.net_income.toFixed(2)}`;

      populateTransactionsTable(data.transactions);
    })
    .catch((error) => console.error("Error fetching report data:", error));

  fetch(`/api/chart-data?start_date=${startDate}&end_date=${endDate}`)
    .then((response) => response.json())
    .then((data) => {
      createExpenseCategoryChart(data);
    })
    .catch((error) => console.error("Error fetching chart data:", error));
}

function createExpenseCategoryChart(categories) {
  const ctx = document
    .getElementById("expense-category-chart")
    .getContext("2d");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: Object.keys(categories),
      datasets: [
        {
          data: Object.values(categories),
          backgroundColor: [
            "#FF6384",
            "#36A2EB",
            "#FFCE56",
            "#4BC0C0",
            "#9966FF",
            "#FF9F40",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      title: {
        display: true,
        text: "Expense Categories",
      },
    },
  });
}

function populateTransactionsTable(transactions) {
  const tbody = document.querySelector("#transactions tbody");
  tbody.innerHTML = "";
  transactions.forEach((transaction) => {
    const row = tbody.insertRow();
    row.insertCell(0).textContent = new Date(
      transaction.date
    ).toLocaleDateString();
    row.insertCell(1).textContent = transaction.type;
    row.insertCell(2).textContent = `$${transaction.amount.toFixed(2)}`;
    row.insertCell(3).textContent = transaction.description;
    row.insertCell(4).textContent = transaction.category || "-";
  });
}

function setupFormValidation() {
  const forms = ["income-form", "expense-form", "register-form", "login-form"];
  forms.forEach((formId) => {
    const form = document.getElementById(formId);
    if (form) {
      form.addEventListener("submit", function (event) {
        if (!validateForm(this)) {
          event.preventDefault();
        }
      });
    }
  });
}

function validateForm(form) {
  let isValid = true;
  form.querySelectorAll("input, select").forEach((input) => {
    if (input.hasAttribute("required") && !input.value) {
      isValid = false;
      showError(input, "This field is required");
    } else if (input.type === "number" && parseFloat(input.value) < 0) {
      isValid = false;
      showError(input, "Value must be positive");
    } else if (input.type === "email" && !isValidEmail(input.value)) {
      isValid = false;
      showError(input, "Invalid email format");
    } else if (
      input.id === "confirm_password" &&
      input.value !== form.querySelector("#password").value
    ) {
      isValid = false;
      showError(input, "Passwords do not match");
    } else {
      clearError(input);
    }
  });
  return isValid;
}

function isValidEmail(email) {
  const re =
    /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

function showError(input, message) {
  clearError(input);
  const error = document.createElement("span");
  error.className = "error";
  error.textContent = message;
  input.parentNode.insertBefore(error, input.nextSibling);
}

function clearError(input) {
  const error = input.parentNode.querySelector(".error");
  if (error) {
    error.remove();
  }
}
