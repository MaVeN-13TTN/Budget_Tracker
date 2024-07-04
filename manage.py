"""Script to manage database migrations and other command-line tasks."""

from flask.cli import FlaskGroup
from app import app, db
from models.budget import User, Income, Expense, Category

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    """Create the database tables."""
    db.create_all()
    print("Database tables created.")


@cli.command("drop_db")
def drop_db():
    """Drop all database tables."""
    db.drop_all()
    print("Database tables dropped.")


@cli.command("seed_db")
def seed_db():
    """Seed the database with initial data."""
    # Add a sample user
    user = User(username="sample_user", email="sample@example.com")
    user.set_password("password123")
    db.session.add(user)

    # Add some sample categories
    categories = ["Food", "Transportation", "Entertainment", "Utilities"]
    for cat_name in categories:
        category = Category(name=cat_name)
        db.session.add(category)

    db.session.commit()
    print("Database seeded with initial data.")


if __name__ == "__main__":
    cli()
