"""User model with roles and secure password handling."""
from __future__ import annotations

import enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager
from app.utils.timeutil import utcnow


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.USER, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    requests = db.relationship(
        "BookRequest",
        foreign_keys="BookRequest.user_id",
        back_populates="user",
        lazy="dynamic",
    )
    loans = db.relationship("Loan", back_populates="user", lazy="dynamic")

    # --- password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # --- convenience ------------------------------------------------------
    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_active(self) -> bool:  # used by Flask-Login
        return self.active

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))
