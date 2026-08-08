"""Book service tests."""
import pytest

from app.services import book_service
from app.services.exceptions import (
    BookInUseError,
    DuplicateISBNError,
    ServiceError,
)


def _make_book(**overrides):
    data = dict(
        isbn="111", title="Test Book", author="Author", total_copies=3,
        available_copies=3,
    )
    data.update(overrides)
    return book_service.create_book(**data)


def test_add_book(app):
    book = _make_book()
    assert book.id is not None
    assert book.available_copies == 3


def test_duplicate_isbn(app):
    _make_book(isbn="dup")
    with pytest.raises(DuplicateISBNError):
        _make_book(isbn="dup")


def test_title_mandatory(app):
    with pytest.raises(ServiceError):
        book_service.create_book(isbn="x", title="", author="A", total_copies=1)


def test_available_cannot_exceed_total(app):
    with pytest.raises(ServiceError):
        book_service.create_book(
            isbn="x", title="T", author="A", total_copies=1, available_copies=5
        )


def test_edit_book(app):
    book = _make_book()
    updated = book_service.update_book(book.id, title="New Title")
    assert updated.title == "New Title"


def test_delete_book(app):
    book = _make_book()
    book_service.delete_book(book.id)
    assert book_service.list_books() == []


def test_cannot_delete_issued_book(app):
    book = _make_book(total_copies=2, available_copies=1)  # 1 issued
    with pytest.raises(BookInUseError):
        book_service.delete_book(book.id)


def test_search_by_title(app):
    _make_book(isbn="a", title="Python Basics")
    _make_book(isbn="b", title="Java Basics")
    results = book_service.search_books(q="python")
    assert len(results) == 1
    assert results[0].title == "Python Basics"


def test_filter_available_only(app):
    _make_book(isbn="a", total_copies=1, available_copies=0)
    _make_book(isbn="b", total_copies=1, available_copies=1)
    results = book_service.search_books(available_only=True)
    assert len(results) == 1
