"""Book model."""
from __future__ import annotations

from app.extensions import db
from app.utils.timeutil import utcnow


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False, index=True)
    publisher = db.Column(db.String(255))
    category = db.Column(db.String(100), index=True)
    publication_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, default=0, nullable=False)
    available_copies = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    requests = db.relationship("BookRequest", back_populates="book", lazy="dynamic")
    loans = db.relationship("Loan", back_populates="book", lazy="dynamic")

    __table_args__ = (
        db.CheckConstraint("total_copies >= 0", name="ck_total_copies_non_negative"),
        db.CheckConstraint(
            "available_copies <= total_copies", name="ck_available_lte_total"
        ),
        db.CheckConstraint("available_copies >= 0", name="ck_available_non_negative"),
    )

    @property
    def issued_copies(self) -> int:
        return self.total_copies - self.available_copies

    @property
    def is_available(self) -> bool:
        return self.available_copies > 0

    def __repr__(self) -> str:
        return f"<Book {self.title!r} ({self.isbn})>"
