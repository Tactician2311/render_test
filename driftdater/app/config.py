"""
app/config.py
-------------
Application configuration loaded from environment variables.

All sensitive values (SECRET_KEY, DATABASE_URL) should be set in a `.env`
file at the project root.  A `.env.sample` file is provided as a template.

Environment Variables
---------------------
SECRET_KEY   : Used to sign JWT tokens and Flask sessions.
               Must be a long, random string in production.
DATABASE_URL : Full database connection string.
               Defaults to a local SQLite file for development.
               Set to a PostgreSQL URL for production (e.g. on Render).
UPLOAD_FOLDER: Directory for uploaded profile photos.
               Defaults to an `uploads/` folder beside the app package.
"""

import os
from dotenv import load_dotenv

# Load variables from .env if it exists (development convenience)
load_dotenv()


class Config(object):
    """Base configuration object shared by all environments."""

    DEBUG = False

    # Secret key for signing JWT tokens — override in production via .env
    SECRET_KEY = os.environ.get('SECRET_KEY', 'D4-s3cr3t-K3y-Drift!2026')

    # Directory where uploaded profile photos are stored
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')

    # Database connection string.
    # The .replace() call normalises old Heroku-style `postgres://` URLs to
    # the `postgresql://` scheme required by SQLAlchemy 1.4+.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL', 'sqlite:///driftdater.db')
        .replace('postgres://', 'postgresql://')
    )

    # Suppress the SQLAlchemy modification tracking warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limit uploaded file size to 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Cookie hardening (not used for JWT auth, but kept for any Flask session use)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
