import os
from pymongo import MongoClient
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.digital_library

async def get_db():
    return database

def get_user_collection():
    return database.get_collection("users")

def get_book_collection():
    return database.get_collection("books")
