"""
Main application module for the Budget Tracker app.
"""

# pylint: disable=not-callable

from datetime import datetime, timedelta

import pymysql
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.urls import url_parse
from sqlalchemy import func
from config import Config
from extensions import db, login_manager
from forms import LoginForm, RegistrationForm, IncomeForm, ExpenseForm
from models.budget import User, Income, Expense, Category

pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


@app.route("/")
@login_required
def index():
    """Render the index page."""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for("index"))


@app.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    """Handle adding new income."""
    form = IncomeForm()
    if form.validate_on_submit():
        income = Income(
            amount=form.amount.data,
            source=form.source.data,
            date=form.date.data,
            user=current_user,
        )
        db.session.add(income)
        db.session.commit()
        flash("Income added successfully!")
        return redirect(url_for("index"))
    return render_template("income.html", title="Add Income", form=form)


@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    """Handle adding new expense."""
    form = ExpenseForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by("name")]
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            category_id=form.category.data,
            user=current_user,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!")
        return redirect(url_for("index"))
    return render_template("expenses.html", title="Add Expense", form=form)


@app.route("/reports")
@login_required
def reports():
    """Render the financial reports page."""
    return render_template("reports.html", title="Financial Reports")


@app.route("/api/summary")
@login_required
def api_summary():
    """Retrieve summary data for the current user."""
    total_income = (
        db.session.query(func.sum(Income.amount))
        .filter(Income.user_id == current_user.id)
        .scalar()
        or 0
    )
    total_expenses = (
        db.session.query(func.sum(Expense.amount))
        .filter(Expense.user_id == current_user.id)
        .scalar()
        or 0
    )

    expense_categories = (
        db.session.query(Category.name, func.sum(Expense.amount))
        .join(Expense)
        .filter(Expense.user_id == current_user.id)
        .group_by(Category.name)
        .all()
    )

    expense_category_data = {cat: float(amount) for cat, amount in expense_categories}

    return jsonify(
        {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "expense_categories": expense_category_data,
        }
    )


@app.route("/api/recent_transactions")
@login_required
def api_recent_transactions():
    """Retrieve recent transactions for the current user."""
    recent_incomes = (
        Income.query.filter_by(user_id=current_user.id)
        .order_by(Income.date.desc())
        .limit(5)
        .all()
    )
    recent_expenses = (
        Expense.query.filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc())
        .limit(5)
        .all()
    )

    transactions = [
        {
            "date": income.date.strftime("%Y-%m-%d"),
            "type": "Income",
            "amount": float(income.amount),
            "description": income.source,
        }
        for income in recent_incomes
    ] + [
        {
            "date": expense.date.strftime("%Y-%m-%d"),
            "type": "Expense",
            "amount": float(expense.amount),
            "description": expense.description,
        }
        for expense in recent_expenses
    ]

    transactions.sort(
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True
    )
    return jsonify(transactions[:10])


@app.route("/api/report_data")
@login_required
def get_report_data():
    """Retrieve report data for a specified date range."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # If dates are not provided, use the last 30 days as default
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    incomes = Income.query.filter(
        Income.user == current_user, Income.date >= start_date, Income.date <= end_date
    ).all()
    expenses = Expense.query.filter(
        Expense.user == current_user,
        Expense.date >= start_date,
        Expense.date <= end_date,
    ).all()

    total_income = sum(income.amount for income in incomes)
    total_expenses = sum(expense.amount for expense in expenses)
    net_income = total_income - total_expenses

    transactions = []
    for income in incomes:
        transactions.append(
            {
                "date": income.date.strftime("%Y-%m-%d"),
                "type": "Income",
                "amount": float(income.amount),
                "description": income.source,
                "category": "",
            }
        )
    for expense in expenses:
        transactions.append(
            {
                "date": expense.date.strftime("%Y-%m-%d"),
                "type": "Expense",
                "amount": float(expense.amount),
                "description": expense.description,
                "category": expense.category.name if expense.category else "",
            }
        )

    report_data = {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "net_income": float(net_income),
        "transactions": transactions,
    }

    return jsonify(report_data)


@app.route("/api/chart-data")
@login_required
def chart_data():
    """Retrieve chart data for a specified date range."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # If dates are not provided, use the last 30 days as default
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    expenses = Expense.query.filter(
        Expense.user == current_user,
        Expense.date >= start_date,
        Expense.date <= end_date,
    ).all()
    data = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        data[category_name] = data.get(category_name, 0) + expense.amount

    return jsonify({k: float(v) for k, v in data.items()})


if __name__ == "__main__":
    app.run(debug=True)
