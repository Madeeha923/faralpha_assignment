import re

import mongomock
import pytest

from app import create_app


@pytest.fixture
def app():
    client = mongomock.MongoClient()
    application = create_app(
        {
            "TESTING": True,
            "MONGODB_CLIENT": client,
            "MONGODB_DATABASE": "test_flask_assignment",
        }
    )
    yield application
    client.close()


@pytest.fixture
def client(app):
    return app.test_client()


def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_home_contains_welcome_message_and_time(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert body.startswith("Welcome to the Flask app! The current time is: ")
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", body)


def test_get_data_returns_empty_json_array(client):
    response = client.get("/data")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


def test_post_data_inserts_document_and_returns_id(client, app):
    payload = {"name": "Madeeha", "role": "AI Engineer"}
    response = client.post("/data", json=payload)

    assert response.status_code == 201
    inserted_id = response.get_json()["inserted_id"]
    assert response.get_json()["status"] == "created"
    stored_document = app.extensions["mongo_db"]["data"].find_one({"name": "Madeeha"})
    assert stored_document is not None
    assert str(stored_document["_id"]) == inserted_id
    assert stored_document["role"] == "AI Engineer"


def test_get_data_retrieves_inserted_document_with_string_id(client):
    client.post("/data", json={"name": "Madeeha"})

    response = client.get("/data")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["name"] == "Madeeha"
    assert isinstance(response.get_json()[0]["_id"], str)


def test_multiple_documents_are_stored_and_retrieved(client):
    client.post("/data", json={"name": "Madeeha"})
    client.post("/data", json={"name": "Ada"})

    response = client.get("/data")

    assert response.status_code == 200
    documents = response.get_json()
    assert len(documents) == 2
    assert {document["name"] for document in documents} == {"Madeeha", "Ada"}
    assert all(isinstance(document["_id"], str) for document in documents)


def test_post_data_rejects_malformed_json(client):
    response = client.post("/data", data='{"name":', content_type="application/json")
    assert response.status_code == 400
    assert response.is_json


def test_post_data_rejects_empty_request_body(client):
    response = client.post("/data", data="", content_type="application/json")
    assert response.status_code == 400
    assert response.is_json


def test_post_data_rejects_non_object_json(client):
    response = client.post("/data", json=["not", "an", "object"])
    assert response.status_code == 400
    assert response.is_json


def test_post_data_rejects_empty_object(client):
    response = client.post("/data", json={})
    assert response.status_code == 400
    assert response.is_json


def test_post_data_requires_json_content_type(client):
    response = client.post("/data", data='{"name":"Madeeha"}')
    assert response.status_code == 415
    assert response.is_json
