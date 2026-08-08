"""Seed the database with demo data.

DEMO CREDENTIALS (change before any real deployment):
    admin@library.example.com / Admin@123
    alice@library.example.com / User@123
    bob@library.example.com   / User@123
    carol@library.example.com / User@123
"""
from __future__ import annotations

from app import create_app
from app.extensions import db
from app.models import Book, Role, User
from app.services import request_service
from app.services.request_service import approve_request

ADMIN_PASSWORD = "Admin@123"  # noqa: S105 - demo only, documented
USER_PASSWORD = "User@123"  # noqa: S105 - demo only, documented

BOOKS = [
    ("978-0132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", "Software", 2008, 4),
    ("978-0201633610", "Design Patterns", "Erich Gamma", "Addison-Wesley", "Software", 1994, 3),
    ("978-1491950296", "Building Microservices", "Sam Newman", "O'Reilly", "Architecture", 2015, 5),
    ("978-0596007126", "Head First Design Patterns", "Eric Freeman", "O'Reilly", "Software", 2004, 2),
    ("978-0134685991", "Effective Java", "Joshua Bloch", "Addison-Wesley", "Java", 2018, 4),
    ("978-1593279288", "Python Crash Course", "Eric Matthes", "No Starch", "Python", 2019, 6),
    ("978-1449355739", "Learning Python", "Mark Lutz", "O'Reilly", "Python", 2013, 3),
    ("978-0135957059", "The Pragmatic Programmer", "David Thomas", "Addison-Wesley", "Software", 2019, 4),
    ("978-1617294136", "Grokking Algorithms", "Aditya Bhargava", "Manning", "Algorithms", 2016, 5),
    ("978-0262033848", "Introduction to Algorithms", "Thomas H. Cormen", "MIT Press", "Algorithms", 2009, 2),
]


def run() -> None:
    app = create_app("development")
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(name="Library Admin", email="admin@library.example.com", role=Role.ADMIN)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)

        users = []
        for name, email in [
            ("Alice", "alice@library.example.com"),
            ("Bob", "bob@library.example.com"),
            ("Carol", "carol@library.example.com"),
        ]:
            u = User(name=name, email=email, role=Role.USER)
            u.set_password(USER_PASSWORD)
            db.session.add(u)
            users.append(u)

        for isbn, title, author, pub, cat, year, copies in BOOKS:
            db.session.add(
                Book(
                    isbn=isbn, title=title, author=author, publisher=pub,
                    category=cat, publication_year=year,
                    total_copies=copies, available_copies=copies,
                )
            )
        db.session.commit()

        # a few sample requests
        alice, bob = users[0], users[1]
        clean_code = db.session.query(Book).filter_by(title="Clean Code").first()
        python_cc = db.session.query(Book).filter_by(title="Python Crash Course").first()
        micro = db.session.query(Book).filter_by(title="Building Microservices").first()

        req1 = request_service.create_request(alice, clean_code.id)
        request_service.create_request(bob, python_cc.id)  # stays pending
        req3 = request_service.create_request(alice, micro.id)

        # approve two so we have issued books
        approve_request(req1.id, admin)
        approve_request(req3.id, admin)

        print("Seed complete.")
        print("  Admin: admin@library.example.com /", ADMIN_PASSWORD)
        print("  Users: alice|bob|carol@library.example.com /", USER_PASSWORD)
        print("  CHANGE THESE PASSWORDS before any real use.")


if __name__ == "__main__":
    run()
