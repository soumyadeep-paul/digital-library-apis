from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import Reservation, ReminderRequest
from ..notifications import send_notification

router = APIRouter()

@router.get("/", response_model=List[Reservation])
async def list_reservations(borrower_id: str = None, owner_id: str = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Lists all reservations. Can be filtered by borrower_id or owner_id.
    """
    reservation_collection = db.get_collection("reservations")
    query = {}
    if borrower_id:
        query["borrower_id"] = ObjectId(borrower_id)
    if owner_id:
        query["owner_id"] = ObjectId(owner_id)

    reservations = await reservation_collection.find(query).to_list(100)
    return [Reservation(**reservation) for reservation in reservations]

@router.post("/{reservation_id}/remind", status_code=status.HTTP_200_OK)
async def send_return_reminder(reservation_id: str, req: ReminderRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Sends a return reminder to the borrower.
    """
    reservation_collection = db.get_collection("reservations")
    reservation = await reservation_collection.find_one({"_id": ObjectId(reservation_id)})
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation["owner_id"] != req.owner_id:
        raise HTTPException(status_code=401, detail="User is not the owner of the item")

    borrower = await db.get_collection("users").find_one({"_id": reservation["borrower_id"]})
    owner = await db.get_collection("users").find_one({"_id": reservation["owner_id"]})
    if borrower and owner:
        book = await db.get_collection("books").find_one({"_id": reservation["item_id"]})
        book_title = book['title'] if book else "a book"
        await send_notification(
            db,
            user=User(**borrower),
            cc_user=User(**owner),
            message=f"This is a friendly reminder from {owner['first_name']} to return the book '{book_title}'.",
            type="return_reminder"
        )

    return {"message": "Return reminder sent successfully."}
