from os import environ

from flask import Flask


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        HOST=environ.get("APP_HOST", "0.0.0.0"),
        PORT=int(environ.get("APP_PORT", "5000")),
        MONGODB_URI=environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
        MONGODB_DATABASE=environ.get("MONGODB_DATABASE", "flask_assignment"),
    )

    if test_config:
        app.config.update(test_config)

    from app.database import initialize_database

    initialize_database(app)

    from app.routes import register_routes

    register_routes(app)
    return app
