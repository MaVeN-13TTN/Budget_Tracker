// Global variables
let expenseCategoryChart = null;

document.addEventListener("DOMContentLoaded", function () {
  // Function to get the current page name from the URL
  function getCurrentPage() {
    const path = window.location.pathname;
    const page = path.split("/").pop();
    return page || "index"; // Default to "index" if path is "/"
  }

  const currentPage = getCurrentPage();

  // Functions to run on the home page (index)
  if (currentPage === "" || currentPage === "index") {
    if (document.getElementById("summary")) {
      fetchSummaryData();
      fetchRecentTransactions();
      createSpendingPatternChart();
      checkBudgetAlerts();
      setInterval(checkBudgetAlerts, 3600000); // Check every hour
    }
  }

  // Functions to run on the reports page
  if (currentPage === "reports") {
    if (document.getElementById("date-range")) {
      // Set default date range (last 30 days)
      const today = new Date();
      const thirtyDaysAgo = new Date(
        today.getTime() - 30 * 24 * 60 * 60 * 1000
      );

      document.getElementById("start-date").value = formatDate(thirtyDaysAgo);
      document.getElementById("end-date").value = formatDate(today);

      document
        .getElementById("update-report")
        .addEventListener("click", updateReport);

      // Initial report load
      updateReport();
    }
  }

  // Setup form validation
  setupFormValidation();
});

function formatDate(date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function fetchSummaryData() {
  fetch("/api/summary")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById(
        "total-income"
      ).textContent = `KSH ${data.total_income.toFixed(2)}`;
      document.getElementById(
        "total-expenses"
      ).textContent = `KSH ${data.total_expenses.toFixed(2)}`;
      document.getElementById("balance").textContent = `KSH ${(
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
        row.insertCell(2).textContent = `KSH ${transaction.amount.toFixed(2)}`;
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
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data) {
        throw new Error("No data received from the server");
      }

      // Update summary
      if (data.total_income !== undefined) {
        document.getElementById(
          "report-total-income"
        ).textContent = `KSH ${parseFloat(data.total_income).toFixed(2)}`;
      }
      if (data.total_expenses !== undefined) {
        document.getElementById(
          "report-total-expenses"
        ).textContent = `KSH ${parseFloat(data.total_expenses).toFixed(2)}`;
      }
      if (data.net_income !== undefined) {
        document.getElementById(
          "report-net-income"
        ).textContent = `KSH ${parseFloat(data.net_income).toFixed(2)}`;
      }

      // Update transactions table
      if (Array.isArray(data.transactions)) {
        populateTransactionsTable(data.transactions);
      } else {
        console.error("Transactions data is not an array:", data.transactions);
      }

      // Update expense category chart
      if (
        data.expense_categories &&
        typeof data.expense_categories === "object"
      ) {
        updateExpenseCategoryChart(data.expense_categories);
      } else {
        console.error(
          "Expense categories data is invalid:",
          data.expense_categories
        );
        // Clear the chart if data is invalid
        if (expenseCategoryChart) {
          expenseCategoryChart.destroy();
          expenseCategoryChart = null;
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching report data:", error);
      // Display error message to the user
      const reportContainer = document.getElementById("report-container");
      if (reportContainer) {
        reportContainer.innerHTML = `<p class="error">Error loading report: ${error.message}</p>`;
      }
    });
}

function updateExpenseCategoryChart(categories) {
  const ctx = document.getElementById("expense-category-chart");
  if (!ctx) {
    console.error("Expense category chart element not found");
    return;
  }

  // Destroy the existing chart if it exists
  if (expenseCategoryChart) {
    expenseCategoryChart.destroy();
  }

  // Clear any previous messages
  const previousMessage = ctx.nextElementSibling;
  if (
    previousMessage &&
    previousMessage.classList.contains("no-data-message")
  ) {
    previousMessage.remove();
  }

  if (!categories || Object.keys(categories).length === 0) {
    console.warn("No expense category data to display");
    ctx.getContext("2d").clearRect(0, 0, ctx.width, ctx.height);
    const message = document.createElement("p");
    message.textContent = "No expense data available for the selected period.";
    message.classList.add("no-data-message");
    ctx.insertAdjacentElement("afterend", message);
    return;
  }

  const categoryNames = Object.keys(categories);
  const categoryValues = Object.values(categories);

  expenseCategoryChart = new Chart(ctx.getContext("2d"), {
    type: "pie",
    data: {
      labels: categoryNames,
      datasets: [
        {
          data: categoryValues,
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
    row.insertCell(2).textContent = `KSH ${transaction.amount.toFixed(2)}`;
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

function createSpendingPatternChart() {
  fetch("/api/spending_patterns")
    .then((response) => {
      if (!response.ok) {
        return response.json().then((err) => {
          throw err;
        });
      }
      return response.json();
    })
    .then((data) => {
      if (data.error) {
        throw new Error(data.error);
      }
      const chartElement = document.getElementById("spending-pattern-chart");
      if (!chartElement) {
        console.error("Spending pattern chart element not found");
        return;
      }
      const ctx = chartElement.getContext("2d");
      const months = Object.keys(data).sort();
      const categories = [
        ...new Set(months.flatMap((month) => Object.keys(data[month]))),
      ];

      const datasets = categories.map((category) => ({
        label: category,
        data: months.map((month) => data[month][category] || 0),
        fill: false,
      }));

      new Chart(ctx, {
        type: "line",
        data: {
          labels: months,
          datasets: datasets,
        },
        options: {
          responsive: true,
          title: {
            display: true,
            text: "Spending Patterns Over Time",
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: "Amount (KSH)",
              },
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error fetching spending patterns:", error);
      const chartContainer = document.getElementById("spending-pattern-chart");
      if (chartContainer) {
        chartContainer.innerHTML = `<p class="error">Error loading spending patterns: ${
          error.message || "Unknown error"
        }</p>`;
      } else {
        console.error("Spending pattern chart container not found");
      }
    });
}

function checkBudgetAlerts() {
  fetch("/api/check_budget_alerts")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((alerts) => {
      const alertContainer = document.getElementById("budget-alerts");
      if (!alertContainer) {
        console.error("Budget alerts container not found");
        return;
      }
      alertContainer.innerHTML = "";
      alerts.forEach((alert) => {
        const alertElement = document.createElement("div");
        alertElement.className = "alert alert-warning";
        alertElement.textContent =
          `Warning: You've exceeded your budget for ${alert.category}. ` +
          `Limit: KSH ${alert.limit.toFixed(
            2
          )}, Spent: KSH ${alert.spent.toFixed(2)} ` +
          `(${alert.percentage.toFixed(1)}%)`;
        alertContainer.appendChild(alertElement);
      });
    })
    .catch((error) => {
      console.error("Error checking budget alerts:", error);
      const alertContainer = document.getElementById("budget-alerts");
      if (alertContainer) {
        alertContainer.innerHTML = `<p class="error">Error checking budget alerts: ${
          error.message || "Unknown error"
        }</p>`;
      } else {
        console.error("Budget alerts container not found");
      }
    });
}
