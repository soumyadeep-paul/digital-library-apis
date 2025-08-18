from pydantic import BaseModel, Field, EmailStr, ConfigDict
from pydantic_core import core_schema
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class Community(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Rating(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    rated_by: PyObjectId

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    first_name: str
    last_name: str
    email: EmailStr
    community_id: PyObjectId
    block_number: str
    flat_number: str
    ratings: List[Rating] = []
    member_since: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    community_id: PyObjectId
    block_number: str
    flat_number: str

class Book(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    authors: List[str]
    isbn: str
    owner_id: PyObjectId
    community_id: PyObjectId
    status: str = "available"
    borrower_id: Optional[PyObjectId] = None
    reservation_pending: bool = False
    return_pending: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    genre: Optional[str] = None
    thumbnail: Optional[str] = None
    return_date: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class BookCreate(BaseModel):
    isbn: str
    owner_id: PyObjectId
    community_id: PyObjectId

class Reservation(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    item_id: PyObjectId
    item_type: str
    borrower_id: PyObjectId
    owner_id: PyObjectId
    reserved_at: datetime = Field(default_factory=datetime.utcnow)
    return_date: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class ReserveRequest(BaseModel):
    borrower_id: PyObjectId
    return_date: datetime

class OwnerConfirmRequest(BaseModel):
    owner_id: PyObjectId

class BorrowerReturnRequest(BaseModel):
    borrower_id: PyObjectId

class ReturnConfirmRequest(BaseModel):
    owner_id: PyObjectId
    rating: int
    comment: Optional[str] = None

class ReminderRequest(BaseModel):
    owner_id: PyObjectId

class Notification(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    message: str
    type: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
