from datetime import datetime

from flask import current_app, jsonify, request
from pymongo.errors import PyMongoError
from werkzeug.exceptions import BadRequest


def register_routes(app):
    @app.get("/")
    def index():
        current_time = datetime.now().astimezone().isoformat(timespec="seconds")
        return f"Welcome to the Flask app! The current time is: {current_time}", 200

    @app.get("/data")
    def get_data():
        from app.database import get_collection

        try:
            documents = list(get_collection(current_app).find())
        except PyMongoError:
            current_app.logger.exception("Could not retrieve data from MongoDB")
            return jsonify(error="Database is unavailable."), 503

        for document in documents:
            document["_id"] = str(document["_id"])
        return jsonify(documents), 200

    @app.post("/data")
    def post_data():
        if not request.is_json:
            return jsonify(error="Content-Type must be application/json."), 415

        try:
            payload = request.get_json()
        except BadRequest:
            return jsonify(error="Request body must contain valid JSON."), 400

        if payload is None:
            return jsonify(error="Request body must contain valid JSON."), 400
        if not isinstance(payload, dict):
            return jsonify(error="JSON body must be an object."), 400
        if not payload:
            return jsonify(error="JSON object must not be empty."), 400

        from app.database import get_collection

        try:
            result = get_collection(current_app).insert_one(payload)
        except PyMongoError:
            current_app.logger.exception("Could not insert data into MongoDB")
            return jsonify(error="Database is unavailable."), 503

        return jsonify(status="created", inserted_id=str(result.inserted_id)), 201
