from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return current_user