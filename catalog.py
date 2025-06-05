# This program provides the API for listing the available books in the catalog and their details.
# It uses the FastAPI framework to create the API endpoints.
# The catalog is stored in a JSON file, and the API reads from this file to provide the book details.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI()

# Load the catalog data from the JSON file
with open("catalog.json", "r") as f:
    catalog_data = json.load(f)

class Book(BaseModel):
    id: int
    title: str
    author: str
    description: str
    available: bool
    thumbnail_url: Optional[str] = None

@app.get("/books", response_model=List[Book])
def list_books():
    return catalog_data

@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    book = next((book for book in catalog_data if book.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# Endpoint to search for books by title or author
@app.get("/search", response_model=List[Book])
def search_books(query: str):
    results = [book for book in catalog_data if query.lower() in book.title.lower() or query.lower() in book.author.lower()]
    if not results:
        raise HTTPException(status_code=404, detail="No books found matching the search criteria")
    return results  

# Endpoint to check if a book is available
@app.get("/books/{book_id}/available", response_model=bool)
def is_book_available(book_id: int):
    book = next((book for book in catalog_data if book.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book.available

# Endpoint to get the thumbnail URL of a book
@app.get("/books/{book_id}/thumbnail", response_model=Optional[str])
def get_book_thumbnail(book_id: int):
    book = next((book for book in catalog_data if book.id == book_id), None)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book.thumbnail_url if book.thumbnail_url else None   

# Endpoint to get the total number of books in the catalog
@app.get("/books/count", response_model=int)
def get_book_count():
    return len(catalog_data)    

# Endpoint to get a list of all authors in the catalog
@app.get("/authors", response_model=List[str])
def list_authors():
    authors = list(set(book.author for book in catalog_data))
    return authors  

# Endpoint to get a list of all book titles in the catalog
@app.get("/titles", response_model=List[str])
def list_titles():
    titles = [book.title for book in catalog_data]
    return titles   

# Endpoint to get a list of all available books
@app.get("/available_books", response_model=List[Book])
def list_available_books():
    available_books = [book for book in catalog_data if book.available]
    return available_books
