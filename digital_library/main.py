from fastapi import FastAPI
from .routers import users, books, communities

app = FastAPI()

app.include_router(users.router, tags=["users"], prefix="/users")
app.include_router(books.router, tags=["books"], prefix="/books")
app.include_router(communities.router, prefix="/communities", tags=["communities"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Digital Library"}
