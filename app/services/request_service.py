"""Business logic for the book request workflow."""
from __future__ import annotations

import logging

from app.extensions import db
from app.models import Book, BookRequest, RequestStatus, User
from app.services import loan_service
from app.services.book_service import get_book
from app.services.exceptions import (
    BookUnavailableError,
    DuplicateRequestError,
    InvalidStateError,
    NotFoundError,
)
from app.utils.timeutil import utcnow

logger = logging.getLogger(__name__)


def get_request(request_id: int) -> BookRequest:
    req = db.session.get(BookRequest, request_id)
    if req is None:
        raise NotFoundError(f"Request {request_id} not found")
    return req


def create_request(user: User, book_id: int) -> BookRequest:
    """A user requests an available book (no duplicate pending requests)."""
    book = get_book(book_id)
    if book.available_copies <= 0:
        raise BookUnavailableError("This book is not currently available")

    existing = (
        db.session.query(BookRequest)
        .filter_by(user_id=user.id, book_id=book_id, status=RequestStatus.PENDING)
        .first()
    )
    if existing:
        raise DuplicateRequestError("You already have a pending request for this book")

    req = BookRequest(user_id=user.id, book_id=book_id, status=RequestStatus.PENDING)
    db.session.add(req)
    db.session.commit()
    logger.info("Request created id=%s user=%s book=%s", req.id, user.id, book_id)
    return req


def approve_request(request_id: int, admin: User) -> BookRequest:
    """Approve a pending request and create a loan."""
    req = get_request(request_id)
    if req.status != RequestStatus.PENDING:
        raise InvalidStateError("Only pending requests can be approved")

    book: Book = req.book
    if book.available_copies <= 0:
        raise BookUnavailableError("No copies available to issue")

    req.status = RequestStatus.APPROVED
    req.approved_by = admin.id
    req.approval_date = utcnow()

    loan = loan_service.issue_loan(req)  # decrements available_copies
    db.session.commit()
    logger.info("Request approved id=%s by admin=%s loan=%s", req.id, admin.id, loan.id)
    return req


def reject_request(request_id: int, admin: User, reason: str) -> BookRequest:
    req = get_request(request_id)
    if req.status != RequestStatus.PENDING:
        raise InvalidStateError("Only pending requests can be rejected")
    if not reason or not reason.strip():
        raise InvalidStateError("A rejection reason is required")

    req.status = RequestStatus.REJECTED
    req.approved_by = admin.id
    req.approval_date = utcnow()
    req.rejection_reason = reason.strip()
    db.session.commit()
    logger.info("Request rejected id=%s by admin=%s", req.id, admin.id)
    return req


def cancel_request(request_id: int, user: User) -> BookRequest:
    req = get_request(request_id)
    if req.user_id != user.id:
        raise InvalidStateError("Cannot cancel another user's request")
    if req.status != RequestStatus.PENDING:
        raise InvalidStateError("Only pending requests can be cancelled")
    req.status = RequestStatus.CANCELLED
    db.session.commit()
    return req


def pending_requests() -> list[BookRequest]:
    return (
        db.session.query(BookRequest)
        .filter_by(status=RequestStatus.PENDING)
        .order_by(BookRequest.request_date)
        .all()
    )


def requests_for_user(user_id: int) -> list[BookRequest]:
    return (
        db.session.query(BookRequest)
        .filter_by(user_id=user_id)
        .order_by(BookRequest.request_date.desc())
        .all()
    )
