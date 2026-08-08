"""Book request (reservation) model."""
from __future__ import annotations

import enum

from app.extensions import db
from app.utils.timeutil import utcnow


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class BookRequest(db.Model):
    __tablename__ = "book_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    request_date = db.Column(db.DateTime, default=utcnow, nullable=False)
    status = db.Column(
        db.Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True
    )
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    user = db.relationship("User", foreign_keys=[user_id], back_populates="requests")
    book = db.relationship("Book", back_populates="requests")
    approver = db.relationship("User", foreign_keys=[approved_by])
    loan = db.relationship("Loan", back_populates="request", uselist=False)

    def __repr__(self) -> str:
        return f"<BookRequest u={self.user_id} b={self.book_id} {self.status.value}>"
