"""Business logic for books."""
from __future__ import annotations

import logging

from sqlalchemy import or_

from app.extensions import db
from app.models import Book
from app.services.exceptions import (
    BookInUseError,
    DuplicateISBNError,
    NotFoundError,
    ServiceError,
)

logger = logging.getLogger(__name__)


def get_book(book_id: int) -> Book:
    book = db.session.get(Book, book_id)
    if book is None:
        raise NotFoundError(f"Book {book_id} not found")
    return book


def create_book(**data) -> Book:
    """Create a book, enforcing unique ISBN and copy invariants."""
    isbn = (data.get("isbn") or "").strip()
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()

    if not title:
        raise ServiceError("Title is mandatory")
    if not author:
        raise ServiceError("Author is mandatory")

    if db.session.query(Book).filter_by(isbn=isbn).first():
        raise DuplicateISBNError(f"A book with ISBN {isbn} already exists")

    total = int(data.get("total_copies", 0))
    if total < 0:
        raise ServiceError("total_copies must be >= 0")

    available = int(data.get("available_copies", total))
    if available > total:
        raise ServiceError("available_copies cannot exceed total_copies")

    book = Book(
        isbn=isbn,
        title=title,
        author=author,
        publisher=(data.get("publisher") or "").strip() or None,
        category=(data.get("category") or "").strip() or None,
        publication_year=data.get("publication_year") or None,
        total_copies=total,
        available_copies=available,
        description=data.get("description"),
    )
    db.session.add(book)
    db.session.commit()
    logger.info("Book added id=%s title=%r", book.id, book.title)
    return book


def update_book(book_id: int, **data) -> Book:
    book = get_book(book_id)
    new_isbn = (data.get("isbn") or book.isbn).strip()
    if new_isbn != book.isbn:
        if db.session.query(Book).filter_by(isbn=new_isbn).first():
            raise DuplicateISBNError(f"A book with ISBN {new_isbn} already exists")
        book.isbn = new_isbn

    if "title" in data and data["title"]:
        book.title = data["title"].strip()
    if "author" in data and data["author"]:
        book.author = data["author"].strip()
    for field in ("publisher", "category", "description"):
        if field in data:
            book.__setattr__(field, data[field])
    if "publication_year" in data:
        book.publication_year = data["publication_year"] or None

    if "total_copies" in data and data["total_copies"] is not None:
        new_total = int(data["total_copies"])
        if new_total < 0:
            raise ServiceError("total_copies must be >= 0")
        # keep available in sync with issued copies
        issued = book.issued_copies
        if new_total < issued:
            raise ServiceError(
                f"Cannot set total below {issued} currently-issued copies"
            )
        book.available_copies = new_total - issued
        book.total_copies = new_total

    db.session.commit()
    logger.info("Book updated id=%s", book.id)
    return book


def delete_book(book_id: int) -> None:
    """Delete a book unless copies are currently issued."""
    book = get_book(book_id)
    if book.issued_copies > 0:
        raise BookInUseError("Cannot delete a book while copies are issued")
    db.session.delete(book)
    db.session.commit()
    logger.info("Book removed id=%s title=%r", book_id, book.title)


def search_books(
    q: str | None = None,
    category: str | None = None,
    available_only: bool = False,
) -> list[Book]:
    """Search via SQL rather than loading everything into memory."""
    query = db.session.query(Book)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(like),
                Book.author.ilike(like),
                Book.isbn.ilike(like),
                Book.category.ilike(like),
            )
        )
    if category:
        query = query.filter(Book.category == category)
    if available_only:
        query = query.filter(Book.available_copies > 0)
    return query.order_by(Book.title).all()


def list_books() -> list[Book]:
    return db.session.query(Book).order_by(Book.title).all()
