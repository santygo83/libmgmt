"""Book browsing and search routes (available to logged-in users)."""
from __future__ import annotations

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.extensions import db
from app.models import Book, RequestStatus
from app.services import book_service
from app.services.exceptions import ServiceError

books_bp = Blueprint("books", __name__, url_prefix="/books")


@books_bp.route("/")
@login_required
def browse():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip() or None
    available = request.args.get("available") == "1"
    results = book_service.search_books(
        q=q or None, category=category, available_only=available
    )
    categories = [
        row[0]
        for row in db.session.query(Book.category)
        .filter(Book.category.isnot(None))
        .distinct()
        .all()
    ]
    return render_template(
        "user/browse.html",
        books=results,
        q=q,
        category=category,
        available=available,
        categories=sorted(categories),
    )


@books_bp.route("/<int:book_id>")
@login_required
def detail(book_id: int):
    from flask_login import current_user

    try:
        book = book_service.get_book(book_id)
    except ServiceError:
        return render_template("errors/404.html"), 404

    from app.models import BookRequest

    user_pending = (
        db.session.query(BookRequest)
        .filter_by(
            user_id=current_user.id, book_id=book_id, status=RequestStatus.PENDING
        )
        .first()
        is not None
    )
    return render_template(
        "user/book_detail.html", book=book, user_pending=user_pending
    )


@books_bp.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    results = book_service.search_books(q=q or None)
    return render_template("user/browse.html", books=results, q=q, categories=[])
