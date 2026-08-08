"""Business logic for loans (issuing and returning books)."""
from __future__ import annotations

import logging
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.models import BookRequest, Loan, LoanStatus, RequestStatus
from app.services.exceptions import (
    BookUnavailableError,
    InvalidStateError,
    NotFoundError,
)
from app.utils.timeutil import utcnow

logger = logging.getLogger(__name__)


def _loan_period_days() -> int:
    try:
        return int(current_app.config.get("LOAN_PERIOD_DAYS", 14))
    except RuntimeError:  # outside app context (defensive)
        return 14


def get_loan(loan_id: int) -> Loan:
    loan = db.session.get(Loan, loan_id)
    if loan is None:
        raise NotFoundError(f"Loan {loan_id} not found")
    return loan


def issue_loan(request: BookRequest) -> Loan:
    """Create a loan from an approved request and decrement availability.

    Note: caller (request_service.approve_request) is responsible for the
    commit so the whole approval is atomic.
    """
    book = request.book
    if book.available_copies <= 0:
        raise BookUnavailableError("No copies available to issue")

    issue_date = utcnow()
    due_date = issue_date + timedelta(days=_loan_period_days())

    loan = Loan(
        user_id=request.user_id,
        book_id=request.book_id,
        request_id=request.id,
        issue_date=issue_date,
        due_date=due_date,
        status=LoanStatus.ISSUED,
    )
    book.available_copies -= 1
    db.session.add(loan)
    db.session.flush()  # assign loan.id within the outer transaction
    logger.info("Book issued loan=%s user=%s book=%s", loan.id, loan.user_id, book.id)
    return loan


def return_loan(loan_id: int) -> Loan:
    """Mark a loan returned and restore availability."""
    loan = get_loan(loan_id)
    if loan.status == LoanStatus.RETURNED:
        raise InvalidStateError("This loan has already been returned")

    loan.return_date = utcnow()
    loan.status = LoanStatus.RETURNED
    loan.book.available_copies += 1

    if loan.request and loan.request.status == RequestStatus.APPROVED:
        loan.request.status = RequestStatus.COMPLETED

    db.session.commit()
    logger.info("Book returned loan=%s book=%s", loan.id, loan.book_id)
    return loan


def refresh_overdue() -> int:
    """Flip ISSUED loans past due date to OVERDUE. Returns count updated."""
    now = utcnow()
    overdue = (
        db.session.query(Loan)
        .filter(Loan.status == LoanStatus.ISSUED, Loan.due_date < now)
        .all()
    )
    for loan in overdue:
        loan.status = LoanStatus.OVERDUE
    if overdue:
        db.session.commit()
    return len(overdue)


def active_loans() -> list[Loan]:
    return (
        db.session.query(Loan)
        .filter(Loan.status != LoanStatus.RETURNED)
        .order_by(Loan.issue_date.desc())
        .all()
    )


def loans_for_user(user_id: int) -> list[Loan]:
    return (
        db.session.query(Loan)
        .filter_by(user_id=user_id)
        .order_by(Loan.issue_date.desc())
        .all()
    )


def recent_loans(limit: int = 10) -> list[Loan]:
    return (
        db.session.query(Loan).order_by(Loan.issue_date.desc()).limit(limit).all()
    )
