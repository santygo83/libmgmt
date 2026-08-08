"""Normal-user routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models import LoanStatus, RequestStatus
from app.services import book_service, loan_service, request_service
from app.services.exceptions import ServiceError

user_bp = Blueprint("user", __name__, url_prefix="/me")


@user_bp.before_request
@login_required
def _require_login():
    """All user routes require login."""


@user_bp.route("/")
def dashboard():
    loan_service.refresh_overdue()
    available = book_service.search_books(available_only=True)
    my_requests = request_service.requests_for_user(current_user.id)
    my_loans = loan_service.loans_for_user(current_user.id)
    pending = [r for r in my_requests if r.status == RequestStatus.PENDING]
    active_loans = [loan_service_loan for loan_service_loan in my_loans
                    if loan_service_loan.status != LoanStatus.RETURNED]
    overdue = [loan_ for loan_ in active_loans if loan_.is_overdue]
    return render_template(
        "user/dashboard.html",
        available_count=len(available),
        pending=pending,
        active_loans=active_loans,
        overdue=overdue,
    )


@user_bp.route("/requests")
def my_requests():
    reqs = request_service.requests_for_user(current_user.id)
    return render_template("user/requests.html", requests=reqs)


@user_bp.route("/requests/<int:book_id>/create", methods=["POST"])
def request_book(book_id: int):
    try:
        request_service.create_request(current_user, book_id)
        flash("Request submitted. Await admin approval.", "success")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("books.detail", book_id=book_id))


@user_bp.route("/requests/<int:request_id>/cancel", methods=["POST"])
def cancel_request(request_id: int):
    try:
        request_service.cancel_request(request_id, current_user)
        flash("Request cancelled.", "info")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("user.my_requests"))


@user_bp.route("/books")
def my_books():
    loan_service.refresh_overdue()
    loans = loan_service.loans_for_user(current_user.id)
    active = [loan_ for loan_ in loans if loan_.status != LoanStatus.RETURNED]
    return render_template("user/books.html", loans=active)


@user_bp.route("/history")
def history():
    loans = loan_service.loans_for_user(current_user.id)
    return render_template("user/history.html", loans=loans)


@user_bp.route("/profile")
def profile():
    return render_template("user/profile.html")
