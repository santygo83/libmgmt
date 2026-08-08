"""Aggregate statistics for dashboards."""
from __future__ import annotations

from sqlalchemy import func

from app.extensions import db
from app.models import Book, BookRequest, Loan, RequestStatus, User
from app.utils.timeutil import utcnow


def library_stats() -> dict:
    total_books = db.session.query(func.count(Book.id)).scalar() or 0
    total_copies = db.session.query(func.coalesce(func.sum(Book.total_copies), 0)).scalar()
    available = db.session.query(
        func.coalesce(func.sum(Book.available_copies), 0)
    ).scalar()
    issued = (total_copies or 0) - (available or 0)

    pending = (
        db.session.query(func.count(BookRequest.id))
        .filter(BookRequest.status == RequestStatus.PENDING)
        .scalar()
        or 0
    )
    users = db.session.query(func.count(User.id)).scalar() or 0
    overdue = (
        db.session.query(func.count(Loan.id))
        .filter(
            Loan.return_date.is_(None),
            Loan.due_date < utcnow(),
        )
        .scalar()
        or 0
    )

    return {
        "total_books": total_books,
        "total_copies": total_copies or 0,
        "available_copies": available or 0,
        "issued_copies": issued,
        "pending_requests": pending,
        "users": users,
        "overdue_books": overdue,
    }
