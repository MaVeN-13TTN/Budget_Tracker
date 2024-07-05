"""
Main application module for the Budget Tracker app.
"""

# pylint: disable=not-callable

from datetime import datetime, timedelta


import csv
from io import StringIO
import pymysql

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    make_response,
    abort,
)
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.urls import url_parse
from sqlalchemy import func, extract
from config import Config
from extensions import db, login_manager
from forms import BudgetLimitForm, LoginForm, RegistrationForm, IncomeForm, ExpenseForm
from models.budget import BudgetLimit, User, Income, Expense, Category

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
    """Render the index page with income and expense lists."""
    incomes = (
        Income.query.filter_by(user=current_user).order_by(Income.date.desc()).all()
    )
    expenses = (
        Expense.query.filter_by(user=current_user).order_by(Expense.date.desc()).all()
    )
    return render_template("index.html", incomes=incomes, expenses=expenses)


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


def check_budget_limit(user, category_id, amount):
    """Check if an expense is within the set budget limit."""
    budget_limit = BudgetLimit.query.filter_by(
        user_id=user.id, category_id=category_id
    ).first()
    if not budget_limit:
        return True, None  # No limit set, allow expense

    current_month = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    total_expenses = (
        db.session.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user.id,
            Expense.category_id == category_id,
            Expense.date >= current_month,
        )
        .scalar()
        or 0
    )

    if total_expenses + amount > budget_limit.amount:
        return False, budget_limit.amount
    return True, None


@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    """Handle adding new expense."""
    form = ExpenseForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by("name")]
    if form.validate_on_submit():
        within_limit, limit = check_budget_limit(
            current_user, form.category.data, form.amount.data
        )
        if not within_limit:
            flash(
                f"This expense exceeds your budget limit of ${limit:.2f}. "
                "Please adjust your expense or update your budget limit.",
                "warning",
            )
            return render_template("expenses.html", title="Add Expense", form=form)

        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            category_id=form.category.data,
            user_id=current_user.id,
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

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

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

    # Generate expense categories data
    expense_categories = (
        db.session.query(Category.name, func.sum(Expense.amount))
        .join(Expense)
        .filter(
            Expense.user == current_user,
            Expense.date >= start_date,
            Expense.date <= end_date,
        )
        .group_by(Category.name)
        .all()
    )

    expense_categories_dict = {
        category: float(amount) for category, amount in expense_categories
    }

    report_data = {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "net_income": float(net_income),
        "transactions": transactions,
        "expense_categories": expense_categories_dict,
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


@app.route("/edit_income/<int:income_id>", methods=["GET", "POST"])
@login_required
def edit_income(income_id):
    """
    Edit an existing income entry.

    :param income_id: The ID of the income entry to edit.
    :return: The rendered edit_income.html template or a redirect to the index page.
    """
    income = Income.query.get_or_404(income_id)
    if income.user != current_user:
        abort(403)

    form = IncomeForm(obj=income)

    if form.validate_on_submit():
        form.populate_obj(income)
        db.session.commit()
        flash("Income updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit_income.html", title="Edit Income", form=form, income_id=income_id
    )


@app.route("/delete_income/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    """
    Delete an income entry.

    :param income_id: The ID of the income entry to delete.
    :return: A redirect to the index page.
    """
    income = Income.query.get_or_404(income_id)
    if income.user != current_user:
        abort(403)

    db.session.delete(income)
    db.session.commit()
    flash("Income deleted successfully!", "success")
    return redirect(url_for("index"))


@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    """
    Edit an existing expense entry.

    :param expense_id: The ID of the expense entry to edit.
    :return: The rendered edit_expense.html template or a redirect to the index page.
    """
    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(403)

    form = ExpenseForm(obj=expense)
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by("name")]

    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.description = form.description.data
        expense.date = form.date.data
        expense.category_id = (
            form.category.data
        )  # Assign category_id, not category object
        db.session.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("index"))

    # For GET requests, set the form's category to the current category_id
    if request.method == "GET":
        form.category.data = expense.category_id

    return render_template(
        "edit_expense.html", title="Edit Expense", form=form, expense_id=expense_id
    )


@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    """
    Delete an expense entry.

    :param expense_id: The ID of the expense entry to delete.
    :return: A redirect to the index page.
    """
    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(403)

    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully!", "success")
    return redirect(url_for("index"))


@app.route("/api/spending_patterns")
@login_required
def spending_patterns():
    """Retrieve spending pattern data for the current user over the last 6 months."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        spending_data = (
            db.session.query(
                func.concat(
                    extract("year", Expense.date),
                    "-",
                    func.lpad(extract("month", Expense.date), 2, "0"),
                ).label("month"),
                Category.name.label("category"),
                func.sum(Expense.amount).label("total"),
            )
            .join(Category)
            .filter(
                Expense.user_id == current_user.id,
                Expense.date.between(start_date, end_date),
            )
            .group_by("month", "category")
            .all()
        )

        data = {}
        for item in spending_data:
            month = item.month
            if month not in data:
                data[month] = {}
            data[month][item.category] = float(item.total)

        return jsonify(data)
    except Exception as e:
        print(f"Error in spending_patterns: {str(e)}")
        return (
            jsonify(
                {
                    "error": f"An error occurred while fetching spending patterns: {str(e)}"
                }
            ),
            500,
        )


@app.route("/delete_budget_limit/<int:limit_id>", methods=["POST"])
@login_required
def delete_budget_limit(limit_id):
    """Delete a budget limit."""
    limit = BudgetLimit.query.get_or_404(limit_id)
    if limit.user != current_user:
        abort(403)
    db.session.delete(limit)
    db.session.commit()
    flash("Budget limit deleted successfully!")
    return redirect(url_for("set_budget_limit"))


# Update the set_budget_limit route to handle both GET and POST requests
@app.route("/set_budget_limit", methods=["GET", "POST"])
@login_required
def set_budget_limit():
    """Handle setting of budget limits."""
    form = BudgetLimitForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by("name")]

    if form.validate_on_submit():
        limit = BudgetLimit.query.filter_by(
            user=current_user, category_id=form.category.data
        ).first()
        if limit:
            limit.amount = form.amount.data
        else:
            limit = BudgetLimit(
                user=current_user,
                category_id=form.category.data,
                amount=form.amount.data,
            )
            db.session.add(limit)
        db.session.commit()
        flash("Budget limit set successfully!")
        return redirect(url_for("set_budget_limit"))

    # Fetch existing budget limits for the current user
    budget_limits = BudgetLimit.query.filter_by(user=current_user).all()

    return render_template(
        "set_budget_limit.html", form=form, budget_limits=budget_limits
    )


@app.route("/api/check_budget_alerts")
@login_required
def check_budget_alerts():
    """Check for budget limit alerts."""
    current_month = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    alerts = []

    for limit in current_user.budget_limits:
        total_expenses = (
            db.session.query(func.sum(Expense.amount))
            .filter(
                Expense.user == current_user,
                Expense.category == limit.category,
                Expense.date >= current_month,
            )
            .scalar()
            or 0
        )

        if total_expenses > limit.amount:
            alerts.append(
                {
                    "category": limit.category.name,
                    "limit": limit.amount,
                    "spent": total_expenses,
                    "percentage": (total_expenses / limit.amount) * 100,
                }
            )

    return jsonify(alerts)


# Add this new route to app.py
@app.route("/api/check_budget_limit", methods=["POST"])
@login_required
def api_check_budget_limit():
    """API endpoint to check budget limit before adding an expense."""
    data = request.json
    category_id = data.get("category_id")
    amount = data.get("amount")

    if not category_id or not amount:
        return jsonify({"error": "Missing category_id or amount"}), 400

    within_limit, limit = check_budget_limit(current_user, category_id, float(amount))
    return jsonify(
        {"within_limit": within_limit, "limit": float(limit) if limit else None}
    )


@app.route("/export_data")
@login_required
def export_data():
    """Export user's financial data as a CSV file."""
    output = StringIO()
    writer = csv.writer(output)

    # Write the header row
    writer.writerow(["Date", "Type", "Amount", "Description", "Category"])

    # Write income data
    incomes = Income.query.filter_by(user=current_user).order_by(Income.date).all()
    for income in incomes:
        writer.writerow([income.date, "Income", income.amount, income.source, ""])

    # Write expense data
    expenses = Expense.query.filter_by(user=current_user).order_by(Expense.date).all()
    for expense in expenses:
        writer.writerow(
            [
                expense.date,
                "Expense",
                expense.amount,
                expense.description,
                expense.category.name,
            ]
        )

    # Create the HTTP response with the CSV data
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=budget_data.csv"
    response.headers["Content-type"] = "text/csv"

    return response


if __name__ == "__main__":
    app.run(debug=True)
