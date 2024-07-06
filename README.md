# Budget Tracker

## Project Overview

Budget Tracker is a web application designed to help users manage their finances and track expenses. It provides a user-friendly platform for tracking income, expenses while offering tools to set and manage budget limits for different categories.

## Features

- User-friendly interface for inputting and displaying budget information
- Automatic calculation of total income, total expenses, and available balance
- Income and expense management (add, edit, delete)
- Visual representations of spending patterns and savings goals
- Budget limits and alerts for different categories
- Data export functionality
- Responsive design supporting various devices and screen sizes

## Technologies Used

- Backend:

  - Python
  - Flask (Python web framework)
  - SQLAlchemy (Python SQL toolkit and Object-Relational Mapping)
  - PyMySQL (MySQL database adapter for Python)

- Frontend:

  - HTML
  - CSS
  - JavaScript
  - Chart.js (for data visualization)

- Database:
  - MySQL

## Getting Started

1. Clone the repository:

   ```
   git clone https://github.com/MaVeN-13TTN/budget-tracker.git
   cd budget-tracker
   ```

2. Set up a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up the MySQL database:

   - Create a new MySQL database named `budget_tracker`
   - Update the `DATABASE_URL` in the `.env` file with your MySQL credentials

5. Set up environment variables:

   - Create a `.env` file in the project root and add the following:
     ```
     FLASK_APP=app.py
     FLASK_ENV=development
     DATABASE_URL=mysql://username:password@localhost/budget_tracker
     SECRET_KEY=your_secret_key_here #can be genereted using the keys.py file
     ```

6. Initialize the database:

   ```
   flask db upgrade
   ```

7. Run the application:

   ```
   flask run
   ```

8. Access the application in your web browser at `http://localhost:5000`

## Project Structure

```
budget_tracker/
│
├── app.py
├── config.py
├── forms.py
├── models/
│   ├── __init__.py
│   └── budget.py
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── edit_expense.html
│   ├── edit_income.html
│   ├── expenses.html
│   ├── income.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── reports.html
│   └── set_budget_limit.html
├── requirements.txt
└── README.md
```

## Usage

1. Register for a new account or log in if you already have one.
2. Add your income sources and expenses.
3. View your financial summary on the dashboard.
4. Generate reports and visualizations to analyze your spending habits.
5. Set budget limits for different expense categories.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
