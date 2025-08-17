import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from urllib.parse import urlparse, urlunparse

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
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Digital Library"}


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/users/", json={"username": "testuser", "email": "test@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_existing_email(client: AsyncClient):
    await client.post("/users/", json={"username": "testuser1", "email": "test1@example.com"})
    response = await client.post("/users/", json={"username": "testuser2", "email": "test1@example.com"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_book(client: AsyncClient):
    user_response = await client.post("/users/", json={"username": "bookowner", "email": "owner@example.com"})
    user_id = user_response.json()["id"]

    # A valid ISBN for testing
    isbn = "9780321765723"

    response = await client.post("/books/", json={"isbn": isbn, "owner_id": user_id})
    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == isbn
    assert data["owner_id"] == user_id


@pytest.mark.asyncio
async def test_list_books(client: AsyncClient):
    response = await client.get("/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
