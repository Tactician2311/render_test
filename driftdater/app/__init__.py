"""
app/__init__.py
---------------
Application factory for DriftDater.

Uses the factory pattern (create_app) so that the Flask app instance is
created once, extensions are initialised against it, and then the Blueprint
containing all API routes is registered.  The module-level `app` variable
is what the Flask CLI (and app.py) import.

Extensions
----------
- SQLAlchemy  : ORM / database layer
- Migrate     : Alembic-backed schema migrations  (flask db init/migrate/upgrade)
- LoginManager: Flask-Login session helper (kept for compatibility; auth is JWT-based)
- CORS        : Allows the Vite dev-server (port 5173) to call the API (port 5000)
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from .config import Config

# Extension instances created here so models.py can import `db` without
# triggering a circular import.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    """
    Create and configure the Flask application.

    Returns
    -------
    flask.Flask
        Fully configured application instance with all extensions initialised
        and the API blueprint registered.
    """
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Bind extensions to the app instance
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)

    # Allow cross-origin requests from the Vue dev server
    # Allow both local dev server and the deployed Render frontend.
    # RENDER_FRONTEND_URL is set in Render's environment variables dashboard.
    import os
    frontend_origins = [
        "http://localhost:5173",
        os.environ.get("RENDER_FRONTEND_URL", ""),
    ]
    CORS(flask_app,
         supports_credentials=True,
         origins=[o for o in frontend_origins if o],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Import models inside the factory so Flask-Migrate can detect all tables
    from app import models  # noqa: F401

    # Register the API blueprint — avoids circular imports because the blueprint
    # object does not need the Flask app to exist at definition time
    from app.views import api
    flask_app.register_blueprint(api)

    return flask_app


# Module-level app used by `flask --app app` CLI and app.py entry point
app = create_app()
