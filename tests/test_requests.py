"""Request workflow tests."""
import pytest

from app.models import RequestStatus
from app.services import book_service, request_service
from app.services.exceptions import (
    BookUnavailableError,
    DuplicateRequestError,
    InvalidStateError,
)


def _book(**over):
    data = dict(isbn="1", title="B", author="A", total_copies=1, available_copies=1)
    data.update(over)
    return book_service.create_book(**data)


def test_create_request(app, normal_user):
    book = _book()
    req = request_service.create_request(normal_user, book.id)
    assert req.status == RequestStatus.PENDING


def test_duplicate_pending_request(app, normal_user):
    book = _book(total_copies=2, available_copies=2)
    request_service.create_request(normal_user, book.id)
    with pytest.raises(DuplicateRequestError):
        request_service.create_request(normal_user, book.id)


def test_request_unavailable_book(app, normal_user):
    book = _book(total_copies=1, available_copies=0)
    with pytest.raises(BookUnavailableError):
        request_service.create_request(normal_user, book.id)


def test_approve_request_creates_loan_and_decrements(app, normal_user, admin_user):
    book = _book(total_copies=2, available_copies=2)
    req = request_service.create_request(normal_user, book.id)
    request_service.approve_request(req.id, admin_user)
    assert req.status == RequestStatus.APPROVED
    assert req.loan is not None
    assert book.available_copies == 1


def test_reject_request_requires_reason(app, normal_user, admin_user):
    book = _book()
    req = request_service.create_request(normal_user, book.id)
    with pytest.raises(InvalidStateError):
        request_service.reject_request(req.id, admin_user, "")


def test_reject_request(app, normal_user, admin_user):
    book = _book()
    req = request_service.create_request(normal_user, book.id)
    request_service.reject_request(req.id, admin_user, "Out of stock")
    assert req.status == RequestStatus.REJECTED
    assert req.rejection_reason == "Out of stock"


def test_cannot_approve_already_processed(app, normal_user, admin_user):
    book = _book(total_copies=2, available_copies=2)
    req = request_service.create_request(normal_user, book.id)
    request_service.approve_request(req.id, admin_user)
    with pytest.raises(InvalidStateError):
        request_service.approve_request(req.id, admin_user)
