import isbnlib
import requests
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import Book, BookCreate, ReserveRequest, OwnerConfirmRequest, BorrowerReturnRequest, ReturnConfirmRequest

router = APIRouter()

def get_book_details_from_google_books(isbn):
    """
    Fetches book details from Google Books API.
    """
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "items" in data and data["items"]:
            volume_info = data["items"][0]["volumeInfo"]
            return {
                "description": volume_info.get("description"),
                "genre": volume_info.get("categories", [None])[0],
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"),
            }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Google Books API: {e}")
    return {}

@router.post("/", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Adds a new book to the catalog by its ISBN.
    Fetches book info from isbnlib and Google Books API.
    """
    user_collection = db.get_collection("users")
    book_collection = db.get_collection("books")

    owner = await user_collection.find_one({"_id": book.owner_id})
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    if not isbnlib.is_isbn10(book.isbn) and not isbnlib.is_isbn13(book.isbn):
        raise HTTPException(status_code=400, detail="Invalid ISBN")

    try:
        book_info = isbnlib.meta(book.isbn)
    except Exception:
        raise HTTPException(status_code=404, detail="Book not found for the given ISBN")

    if not book_info:
        raise HTTPException(status_code=404, detail="Book not found for the given ISBN")

    google_books_details = get_book_details_from_google_books(book.isbn)

    new_book = {
        "title": book_info.get("Title", "No Title"),
        "authors": book_info.get("Authors", []),
        "isbn": book.isbn,
        "owner_id": book.owner_id,
        "status": "available",
        "last_updated": datetime.utcnow(),
        "description": google_books_details.get("description"),
        "genre": google_books_details.get("genre"),
        "thumbnail": google_books_details.get("thumbnail"),
    }

    result = await book_collection.insert_one(new_book)
    created_book = await book_collection.find_one({"_id": result.inserted_id})
    return Book(**created_book)

@router.get("/", response_model=List[Book])
async def list_available_books(title: str = None, author: str = None, genre: str = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Lists all available books. Can be filtered by title, author, or genre.
    """
    book_collection = db.get_collection("books")
    query = {"status": "available"}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if author:
        query["authors"] = {"$regex": author, "$options": "i"}
    if genre:
        query["genre"] = {"$regex": genre, "$options": "i"}

    books = await book_collection.find(query).to_list(100)
    return [Book(**book) for book in books]

@router.post("/{book_id}/reserve", status_code=status.HTTP_200_OK)
async def reserve_book(book_id: str, req: ReserveRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Reserves a book for a user.
    """
    user_collection = db.get_collection("users")
    book_collection = db.get_collection("books")
    reservation_collection = db.get_collection("reservations")

    book = await book_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book["status"] != "available":
        raise HTTPException(status_code=409, detail="Book is not available for reservation")

    borrower = await user_collection.find_one({"_id": req.borrower_id})
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")

    await book_collection.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "status": "reserved",
                "borrower_id": req.borrower_id,
                "reservation_pending": True,
                "last_updated": datetime.utcnow()
            }
        },
    )

    await reservation_collection.insert_one({
        "book_id": ObjectId(book_id),
        "borrower_id": req.borrower_id,
        "owner_id": book["owner_id"],
        "reserved_at": datetime.utcnow()
    })

    return {"message": "Book reserved successfully. Waiting for owner confirmation."}

@router.post("/{book_id}/confirm-reservation", status_code=status.HTTP_200_OK)
async def confirm_reservation(book_id: str, req: OwnerConfirmRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Confirms a reservation by the book owner.
    """
    book_collection = db.get_collection("books")
    reservation_collection = db.get_collection("reservations")

    book = await book_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book["owner_id"] != req.owner_id:
        raise HTTPException(status_code=401, detail="User is not the owner of the book")

    if not book.get("reservation_pending"):
        raise HTTPException(status_code=409, detail="No pending reservation for this book")

    await book_collection.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "status": "borrowed",
                "reservation_pending": False,
                "last_updated": datetime.utcnow()
            }
        },
    )

    await reservation_collection.update_one(
        {"book_id": ObjectId(book_id), "borrower_id": book["borrower_id"]},
        {"$set": {"confirmed_at": datetime.utcnow()}}
    )

    return {"message": "Reservation confirmed."}

@router.post("/{book_id}/return", status_code=status.HTTP_200_OK)
async def return_book(book_id: str, req: BorrowerReturnRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Initiates a book return by the borrower.
    """
    book_collection = db.get_collection("books")
    book = await book_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book["borrower_id"] != req.borrower_id:
        raise HTTPException(status_code=401, detail="User is not the borrower of this book")

    if book["status"] != "borrowed":
        raise HTTPException(status_code=409, detail="Book is not currently borrowed")

    await book_collection.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"return_pending": True, "last_updated": datetime.utcnow()}},
    )
    return {"message": "Book return initiated. Waiting for owner confirmation."}

@router.post("/{book_id}/confirm-return", status_code=status.HTTP_200_OK)
async def confirm_return(book_id: str, req: ReturnConfirmRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Confirms a book return by the owner and allows the owner to rate the borrower.
    """
    user_collection = db.get_collection("users")
    book_collection = db.get_collection("books")
    reservation_collection = db.get_collection("reservations")

    book = await book_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book["owner_id"] != req.owner_id:
        raise HTTPException(status_code=401, detail="User is not the owner of the book")

    if not book.get("return_pending"):
        raise HTTPException(status_code=409, detail="No pending return for this book")

    borrower_id = book.get("borrower_id")
    if not borrower_id:
        raise HTTPException(status_code=404, detail="Borrower not found")

    await book_collection.update_one(
        {"_id": ObjectId(book_id)},
        {
            "$set": {
                "status": "available",
                "return_pending": False,
                "last_updated": datetime.utcnow(),
            },
            "$unset": {"borrower_id": ""},
        },
    )

    await reservation_collection.update_one(
        {"book_id": ObjectId(book_id), "borrower_id": borrower_id},
        {"$set": {"returned_at": datetime.utcnow()}}
    )

    rating = {
        "rating": req.rating,
        "comment": req.comment,
        "rated_by": req.owner_id
    }
    await user_collection.update_one(
        {"_id": borrower_id},
        {"$push": {"ratings": rating}}
    )

    return {"message": "Book return confirmed."}
