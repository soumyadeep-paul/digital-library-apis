import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from urllib.parse import urlparse, urlunparse
from bson import ObjectId
from datetime import datetime, timedelta
import requests

from digital_library.main import app
from digital_library.database import get_db
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017/digital_library")

# Create a test-specific database URI
parsed_url = urlparse(MONGO_DETAILS)
_test_db_name = parsed_url.path.lstrip("/") + "_test"
_test_mongo_url = urlunparse(
    (parsed_url.scheme, parsed_url.netloc, f"/{_test_db_name}", "", "", "")
)


@pytest.fixture(scope="function")
async def client():
    _test_client = AsyncIOMotorClient(_test_mongo_url)
    _test_db = _test_client.get_database()

    async def get_test_db():
        return _test_db

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    await _test_client.drop_database(_test_db_name)
    _test_client.close()


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    # Create community and users
    community_response = await client.post("/communities/", json={"name": "Test Community"})
    community_id = community_response.json()["id"]
    await client.post("/users/", json={"first_name": "test1", "last_name": "user1", "email": "test1@example.com", "community_id": community_id, "block_number": "A", "flat_number": "101"})
    await client.post("/users/", json={"first_name": "test2", "last_name": "user2", "email": "test2@example.com", "community_id": community_id, "block_number": "B", "flat_number": "102"})

    # List users
    response = await client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_filter_books(client: AsyncClient, monkeypatch):
    # Mock external calls
    monkeypatch.setattr("digital_library.routers.books.get_book_details_from_google_books", lambda isbn: {"description": "", "genre": "Fiction", "thumbnail": ""})
    monkeypatch.setattr("isbnlib.meta", lambda isbn: {"Title": "Test Book", "Authors": ["Test Author"]})

    # Create user, community, and book
    community_response = await client.post("/communities/", json={"name": "Test Community"})
    community_id = community_response.json()["id"]
    user_response = await client.post("/users/", json={"first_name": "test", "last_name": "user", "email": "test@example.com", "community_id": community_id, "block_number": "A", "flat_number": "101"})
    user_id = user_response.json()["id"]
    await client.post("/books/", json={"isbn": "9780321765723", "owner_id": user_id, "community_id": community_id})

    # Filter by title
    response = await client.get("/books/?title=Test")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Filter by genre
    response = await client.get("/books/?genre=Fiction")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_confirm_return_with_rating(client: AsyncClient, monkeypatch):
    # Mock external calls and notifications
    monkeypatch.setattr("digital_library.routers.books.get_book_details_from_google_books", lambda isbn: {"description": "", "genre": "", "thumbnail": ""})
    monkeypatch.setattr("isbnlib.meta", lambda isbn: {"Title": "Test Book", "Authors": ["Test Author"]})
    monkeypatch.setattr("digital_library.routers.books.send_notification", lambda db, user, message, type, cc_user: None)

    # Create user, community, and book
    community_response = await client.post("/communities/", json={"name": "Test Community"})
    community_id = community_response.json()["id"]
    owner_response = await client.post("/users/", json={"first_name": "owner", "last_name": "user", "email": "owner@example.com", "community_id": community_id, "block_number": "A", "flat_number": "101"})
    owner_id = owner_response.json()["id"]
    borrower_response = await client.post("/users/", json={"first_name": "borrower", "last_name": "user", "email": "borrower@example.com", "community_id": community_id, "block_number": "B", "flat_number": "102"})
    borrower_id = borrower_response.json()["id"]
    book_response = await client.post("/books/", json={"isbn": "9780321765723", "owner_id": owner_id, "community_id": community_id})
    book_id = book_response.json()["id"]

    # Full reservation flow
    await client.post(f"/books/{book_id}/reserve", json={"borrower_id": borrower_id, "return_date": (datetime.utcnow() + timedelta(days=14)).isoformat()})
    await client.post(f"/books/{book_id}/confirm-reservation", json={"owner_id": owner_id})
    await client.post(f"/books/{book_id}/return", json={"borrower_id": borrower_id})

    # Confirm return with rating
    await client.post(f"/books/{book_id}/confirm-return", json={"owner_id": owner_id, "rating": 5, "comment": "Great!"})

    # Verify rating
    user_response = await client.get(f"/users/")
    borrower_data = next(user for user in user_response.json() if user["id"] == borrower_id)
    assert len(borrower_data["ratings"]) == 1
    assert borrower_data["ratings"][0]["rating"] == 5
    assert borrower_data["ratings"][0]["comment"] == "Great!"
