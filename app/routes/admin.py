"""Admin routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.forms import BookForm, RejectForm
from app.models import Role, User
from app.routes.decorators import admin_required
from app.services import book_service, loan_service, request_service, stats_service
from app.services.exceptions import ServiceError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@admin_required
def _guard():
    """All admin routes require an authenticated admin."""


@admin_bp.route("/")
def dashboard():
    loan_service.refresh_overdue()
    stats = stats_service.library_stats()
    recent = loan_service.recent_loans(limit=10)
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


# --- Books ---------------------------------------------------------------
@admin_bp.route("/books")
def books():
    all_books = book_service.list_books()
    return render_template("admin/books.html", books=all_books)


@admin_bp.route("/books/add", methods=["GET", "POST"])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        try:
            book_service.create_book(
                isbn=form.isbn.data,
                title=form.title.data,
                author=form.author.data,
                publisher=form.publisher.data,
                category=form.category.data,
                publication_year=form.publication_year.data,
                total_copies=form.total_copies.data,
                available_copies=form.available_copies.data
                if form.available_copies.data is not None
                else form.total_copies.data,
                description=form.description.data,
            )
            flash("Book added successfully.", "success")
            return redirect(url_for("admin.books"))
        except ServiceError as exc:
            flash(str(exc), "danger")
    return render_template("admin/book_form.html", form=form, mode="add")


@admin_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id: int):
    try:
        book = book_service.get_book(book_id)
    except ServiceError:
        flash("Book not found.", "danger")
        return redirect(url_for("admin.books"))
    form = BookForm(obj=book)
    if form.validate_on_submit():
        try:
            book_service.update_book(
                book_id,
                isbn=form.isbn.data,
                title=form.title.data,
                author=form.author.data,
                publisher=form.publisher.data,
                category=form.category.data,
                publication_year=form.publication_year.data,
                total_copies=form.total_copies.data,
                description=form.description.data,
            )
            flash("Book updated.", "success")
            return redirect(url_for("admin.books"))
        except ServiceError as exc:
            flash(str(exc), "danger")
    return render_template("admin/book_form.html", form=form, mode="edit", book=book)


@admin_bp.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id: int):
    try:
        book_service.delete_book(book_id)
        flash("Book removed.", "success")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.books"))


# --- Requests ------------------------------------------------------------
@admin_bp.route("/requests")
def requests_view():
    pending = request_service.pending_requests()
    reject_form = RejectForm()
    return render_template(
        "admin/requests.html", requests=pending, reject_form=reject_form
    )


@admin_bp.route("/requests/<int:request_id>/approve", methods=["POST"])
def approve_request(request_id: int):
    from flask_login import current_user

    try:
        request_service.approve_request(request_id, current_user)
        flash("Request approved and book issued.", "success")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.requests_view"))


@admin_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
def reject_request(request_id: int):
    from flask_login import current_user

    form = RejectForm()
    reason = form.reason.data if form.validate_on_submit() else request.form.get("reason", "")
    try:
        request_service.reject_request(request_id, current_user, reason or "")
        flash("Request rejected.", "info")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.requests_view"))


# --- Loans ---------------------------------------------------------------
@admin_bp.route("/issued")
def issued_books():
    loan_service.refresh_overdue()
    loans = loan_service.active_loans()
    return render_template("admin/issued.html", loans=loans)


@admin_bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_loan(loan_id: int):
    try:
        loan_service.return_loan(loan_id)
        flash("Book marked as returned.", "success")
    except ServiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.issued_books"))


# --- Users ---------------------------------------------------------------
@admin_bp.route("/users")
def users():
    all_users = db.session.query(User).order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
def toggle_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "danger")
    elif user.role == Role.ADMIN:
        flash("Cannot deactivate an admin account.", "warning")
    else:
        user.active = not user.active
        db.session.commit()
        flash(f"User {'activated' if user.active else 'deactivated'}.", "info")
    return redirect(url_for("admin.users"))
