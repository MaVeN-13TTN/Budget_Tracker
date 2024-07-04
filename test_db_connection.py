"""
Test script for database connection and CRUD operations.
"""

import sys
import os
from datetime import date
from sqlalchemy.exc import SQLAlchemyError
from app import app, db
from models.budget import User, Income, Expense, Category


def test_connection():
    """Test the database connection and perform basic CRUD operations."""
    print("Starting database connection and CRUD tests...")

    try:
        with app.app_context():
            # Test 1: Database Connection
            db.create_all()
            print("Test 1: Successfully connected to the database.")

            # Test 2: Create Operations
            # Create a test user
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("testpassword")
            db.session.add(test_user)
            db.session.commit()
            print("Test 2a: Successfully created a test user.")

            # Create a test category
            test_category = Category(name="Test Category")
            db.session.add(test_category)
            db.session.commit()
            print("Test 2b: Successfully created a test category.")

            # Create a test income
            test_income = Income(
                amount=1000, source="Test Income", date=date.today(), user=test_user
            )
            db.session.add(test_income)
            db.session.commit()
            print("Test 2c: Successfully created a test income.")

            # Create a test expense
            test_expense = Expense(
                amount=500,
                description="Test Expense",
                date=date.today(),
                user=test_user,
                category=test_category,
            )
            db.session.add(test_expense)
            db.session.commit()
            print("Test 2d: Successfully created a test expense.")

            # Test 3: Read Operations
            # Query the test user
            queried_user = User.query.filter_by(username="testuser").first()
            if queried_user and queried_user.username == "testuser":
                print("Test 3a: Successfully queried the test user.")
            else:
                print("Test 3a: Failed to query the test user.")

            # Query the test income
            queried_income = Income.query.filter_by(source="Test Income").first()
            if queried_income and queried_income.amount == 1000:
                print("Test 3b: Successfully queried the test income.")
            else:
                print("Test 3b: Failed to query the test income.")

            # Query the test expense
            queried_expense = Expense.query.filter_by(
                description="Test Expense"
            ).first()
            if queried_expense and queried_expense.amount == 500:
                print("Test 3c: Successfully queried the test expense.")
            else:
                print("Test 3c: Failed to query the test expense.")

            # Test 4: Update Operations
            # Update the test user's email
            queried_user.email = "updated@example.com"
            db.session.commit()
            updated_user = User.query.filter_by(username="testuser").first()
            if updated_user.email == "updated@example.com":
                print("Test 4: Successfully updated the test user's email.")
            else:
                print("Test 4: Failed to update the test user's email.")

            # Test 5: Delete Operations
            # Delete the test expense
            db.session.delete(queried_expense)
            db.session.commit()
            if not Expense.query.filter_by(description="Test Expense").first():
                print("Test 5a: Successfully deleted the test expense.")
            else:
                print("Test 5a: Failed to delete the test expense.")

            # Delete the test income
            db.session.delete(queried_income)
            db.session.commit()
            if not Income.query.filter_by(source="Test Income").first():
                print("Test 5b: Successfully deleted the test income.")
            else:
                print("Test 5b: Failed to delete the test income.")

            # Delete the test category
            db.session.delete(test_category)
            db.session.commit()
            if not Category.query.filter_by(name="Test Category").first():
                print("Test 5c: Successfully deleted the test category.")
            else:
                print("Test 5c: Failed to delete the test category.")

            # Delete the test user
            db.session.delete(updated_user)
            db.session.commit()
            if not User.query.filter_by(username="testuser").first():
                print("Test 5d: Successfully deleted the test user.")
            else:
                print("Test 5d: Failed to delete the test user.")

            print("All tests completed successfully!")

    except SQLAlchemyError as e:
        print(f"An SQLAlchemy error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.args}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_connection()
