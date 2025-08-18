import asyncio
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
import isbnlib

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from digital_library.database import user_collection, book_collection

async def populate_db():
    """
    Populates the database with sample data.
    """
    print("Clearing existing collections...")
    await user_collection.delete_many({})
    await book_collection.delete_many({})
    print("Collections cleared.")

    print("Inserting sample users...")
    users_to_insert = [
        {"_id": ObjectId(), "username": "Alice", "email": "alice@example.com", "member_since": datetime.utcnow()},
        {"_id": ObjectId(), "username": "Bob", "email": "bob@example.com", "member_since": datetime.utcnow()},
    ]
    await user_collection.insert_many(users_to_insert)
    print(f"{len(users_to_insert)} users inserted.")

    alice = await user_collection.find_one({"username": "Alice"})
    bob = await user_collection.find_one({"username": "Bob"})

    print("Inserting sample books...")
    books_to_insert = [
        {"isbn": "978-0321765723", "owner_id": alice["_id"]}, # The Lord of the Rings
        {"isbn": "978-0743273565", "owner_id": bob["_id"]},   # The Great Gatsby
        {"isbn": "978-1400033416", "owner_id": alice["_id"]}, # 1984
    ]

    for book_data in books_to_insert:
        try:
            book_info = isbnlib.meta(book_data["isbn"])
            if not book_info:
                print(f"Could not find info for ISBN: {book_data['isbn']}")
                continue

            new_book = {
                "title": book_info.get("Title", "No Title"),
                "authors": book_info.get("Authors", []),
                "isbn": book_data["isbn"],
                "owner_id": book_data["owner_id"],
                "status": "available",
                "last_updated": datetime.utcnow()
            }
            await book_collection.insert_one(new_book)
            print(f"Inserted book: {new_book['title']}")
        except Exception as e:
            print(f"Failed to process ISBN {book_data['isbn']}: {e}")

    print("Database populated successfully.")


if __name__ == "__main__":
    # Pymongo < 4.0 does not support asyncio, so we need to use a direct sync call here
    # for the script. The FastAPI app will use the async driver.
    load_dotenv()
    MONGO_DETAILS = os.getenv("MONGO_DETAILS")
    client = MongoClient(MONGO_DETAILS)
    db = client.digital_library

    # Re-assign collections for sync script
    user_collection = db.users
    book_collection = db.books

    print("Running database population script...")

    print("Clearing existing collections...")
    user_collection.delete_many({})
    book_collection.delete_many({})
    print("Collections cleared.")

    print("Inserting sample users...")
    users_to_insert = [
        {"username": "Alice", "email": "alice@example.com", "member_since": datetime.utcnow()},
        {"username": "Bob", "email": "bob@example.com", "member_since": datetime.utcnow()},
    ]
    user_result = user_collection.insert_many(users_to_insert)
    print(f"{len(user_result.inserted_ids)} users inserted.")

    alice = user_collection.find_one({"username": "Alice"})
    bob = user_collection.find_one({"username": "Bob"})

    print("Inserting sample books...")
    books_to_insert = [
        {"isbn": "9780321765723", "owner_id": alice["_id"]}, # The C++ Programming Language
        {"isbn": "9780743273565", "owner_id": bob["_id"]},   # The Great Gatsby
        {"isbn": "9781400033416", "owner_id": alice["_id"]}, # 1984
    ]

    for book_data in books_to_insert:
        try:
            book_info = isbnlib.meta(book_data["isbn"])
            if not book_info:
                print(f"Could not find info for ISBN: {book_data['isbn']}")
                continue

            new_book = {
                "title": book_info.get("Title", "No Title"),
                "authors": book_info.get("Authors", []),
                "isbn": book_data["isbn"],
                "owner_id": book_data["owner_id"],
                "status": "available",
                "last_updated": datetime.utcnow()
            }
            book_collection.insert_one(new_book)
            print(f"Inserted book: {new_book['title']}")
        except Exception as e:
            print(f"Failed to process ISBN {book_data['isbn']}: {e}")

    print("Database populated successfully.")
    client.close()
