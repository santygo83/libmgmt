"""Small read-only REST API returning JSON."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app.extensions import db
from app.models import Book
from app.services import book_service
from app.services.exceptions import NotFoundError

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _serialize(book: Book) -> dict:
    return {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "category": book.category,
        "publication_year": book.publication_year,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
    }


@api_bp.route("/health")
def health():
    db_status = "UP"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "DOWN"
    code = 200 if db_status == "UP" else 503
    return jsonify({"status": "UP", "database": db_status}), code


@api_bp.route("/books")
def books():
    all_books = book_service.list_books()
    return jsonify([_serialize(b) for b in all_books])


@api_bp.route("/books/search")
def search():
    q = request.args.get("q", "").strip()
    results = book_service.search_books(q=q or None)
    return jsonify([_serialize(b) for b in results])


@api_bp.route("/books/<int:book_id>")
def book_detail(book_id: int):
    try:
        book = book_service.get_book(book_id)
    except NotFoundError:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(_serialize(book))
