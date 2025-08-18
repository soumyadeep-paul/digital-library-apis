from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_db
from ..models import Community, CommunityCreate

router = APIRouter()

@router.post("/", response_model=Community, status_code=status.HTTP_201_CREATED)
async def create_community(community: CommunityCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Creates a new community.
    """
    community_collection = db.get_collection("communities")
    if await community_collection.find_one({"name": community.name}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Community with this name already exists",
        )

    community_dict = community.dict()
    result = await community_collection.insert_one(community_dict)
    created_community = await community_collection.find_one({"_id": result.inserted_id})

    return Community(**created_community)

@router.get("/", response_model=List[Community])
async def list_communities(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Lists all communities.
    """
    community_collection = db.get_collection("communities")
    communities = await community_collection.find().to_list(100)
    return [Community(**community) for community in communities]
