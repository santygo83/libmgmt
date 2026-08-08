"""Loan tests."""
from datetime import datetime, timedelta

from app.models import LoanStatus
from app.services import book_service, loan_service, request_service


def _issue(app, normal_user, admin_user):
    book = book_service.create_book(
        isbn="1", title="B", author="A", total_copies=2, available_copies=2
    )
    req = request_service.create_request(normal_user, book.id)
    request_service.approve_request(req.id, admin_user)
    return book, req.loan


def test_issue_decrements_available(app, normal_user, admin_user):
    book, loan = _issue(app, normal_user, admin_user)
    assert book.available_copies == 1
    assert loan.status == LoanStatus.ISSUED


def test_due_date_is_14_days(app, normal_user, admin_user):
    _, loan = _issue(app, normal_user, admin_user)
    delta = loan.due_date - loan.issue_date
    assert delta.days == 14


def test_return_increments_available(app, normal_user, admin_user):
    book, loan = _issue(app, normal_user, admin_user)
    loan_service.return_loan(loan.id)
    assert book.available_copies == 2
    assert loan.status == LoanStatus.RETURNED
    assert loan.return_date is not None


def test_overdue_detection(app, normal_user, admin_user):
    _, loan = _issue(app, normal_user, admin_user)
    loan.due_date = datetime.utcnow() - timedelta(days=1)
    assert loan.is_overdue is True
    count = loan_service.refresh_overdue()
    assert count == 1
    assert loan.status == LoanStatus.OVERDUE


def test_return_already_returned_raises(app, normal_user, admin_user):
    _, loan = _issue(app, normal_user, admin_user)
    loan_service.return_loan(loan.id)
    import pytest

    from app.services.exceptions import InvalidStateError

    with pytest.raises(InvalidStateError):
        loan_service.return_loan(loan.id)
