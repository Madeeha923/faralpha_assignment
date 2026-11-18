from pymongo import MongoClient


def initialize_database(app):
    """Attach the MongoDB client and configured database to this Flask app."""
    client = app.config.get("MONGODB_CLIENT")
    if client is None:
        client = MongoClient(app.config["MONGODB_URI"])

    app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = client[app.config["MONGODB_DATABASE"]]


def get_collection(app, collection_name="data"):
    """Return the named collection from the app's configured MongoDB database."""
    return app.extensions["mongo_db"][collection_name]
