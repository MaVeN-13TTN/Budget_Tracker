"""Form classes for the Budget Tracker application."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    FloatField,
    DateField,
    SelectField,
)
from wtforms.validators import NumberRange
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models.budget import User


class LoginForm(FlaskForm):
    """Form for user login."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """Form for user registration."""

    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class IncomeForm(FlaskForm):
    """Form for setting budget limits."""

    amount = FloatField("Amount", validators=[DataRequired()])
    source = StringField("Source", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    submit = SubmitField("Save Income")


class ExpenseForm(FlaskForm):
    """Form for adding,editing and deleting expenses."""

    amount = FloatField("Amount", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    category = SelectField("Category", coerce=int, validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    submit = SubmitField("Save Expense")


class BudgetLimitForm(FlaskForm):
    """Form for adding, editing and deleting budget limits."""

    category = SelectField("Category", coerce=int, validators=[DataRequired()])
    amount = FloatField("Limit Amount", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Set Limit")
