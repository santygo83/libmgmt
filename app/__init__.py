"""Application factory."""
from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, render_template
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, login_manager, migrate


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app.logger.setLevel(level)


def create_app(config_name: str | None = None) -> Flask:
    from config import config_map

    config_name = config_name or os.getenv("FLASK_CONFIG", "default")
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Behind Nginx the real client info arrives in X-Forwarded-* headers.
    # Trust one proxy hop so url_for(_external), request.scheme and remote_addr
    # reflect the original request rather than the local socket.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    _configure_logging(app)

    # import models so they register with SQLAlchemy metadata
    from app import models  # noqa: F401

    # register blueprints
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)  # read-only JSON API

    _register_health(app)
    _register_error_handlers(app)

    return app


def _register_health(app: Flask) -> None:
    @app.route("/health")
    def health():
        db_status = "UP"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            db_status = "DOWN"
        payload = {"status": "UP", "database": db_status}
        code = 200 if db_status == "UP" else 503
        return jsonify(payload), code


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        # Do not leak stack traces to end users.
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500
