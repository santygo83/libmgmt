"""Loan / issue model."""
from __future__ import annotations

import enum

from app.extensions import db
from app.utils.timeutil import utcnow


class LoanStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    request_id = db.Column(
        db.Integer, db.ForeignKey("book_requests.id"), nullable=True
    )
    issue_date = db.Column(db.DateTime, default=utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.Enum(LoanStatus), default=LoanStatus.ISSUED, nullable=False, index=True
    )

    user = db.relationship("User", back_populates="loans")
    book = db.relationship("Book", back_populates="loans")
    request = db.relationship("BookRequest", back_populates="loan")

    @property
    def is_overdue(self) -> bool:
        """A loan is overdue if not returned and past its due date."""
        return self.return_date is None and utcnow() > self.due_date

    @property
    def effective_status(self) -> LoanStatus:
        """Compute status on the fly (handles overdue transition)."""
        if self.status == LoanStatus.ISSUED and self.is_overdue:
            return LoanStatus.OVERDUE
        return self.status

    def __repr__(self) -> str:
        return f"<Loan u={self.user_id} b={self.book_id} {self.status.value}>"
