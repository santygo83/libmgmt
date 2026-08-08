"""Model package. Import all models so SQLAlchemy/Alembic can discover them."""
from app.models.book import Book
from app.models.loan import Loan, LoanStatus
from app.models.request import BookRequest, RequestStatus
from app.models.user import Role, User

__all__ = [
    "Book",
    "Loan",
    "LoanStatus",
    "BookRequest",
    "RequestStatus",
    "Role",
    "User",
]
