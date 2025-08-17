from fastapi import APIRouter, HTTPException, status, Depends
from ..database import get_db
from ..models import User, UserCreate
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Creates a new user.
    """
    user_collection = db.get_collection("users")
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_dict = user.dict()
    result = await user_collection.insert_one(user_dict)
    created_user = await user_collection.find_one({"_id": result.inserted_id})

    return User(**created_user)
