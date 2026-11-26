from fastapi import APIRouter, Depends
from ..core.security import current_user
from ..state import app_state

router = APIRouter(prefix="/api/v1", tags=["leaderboard"])

@router.get("/leaderboard")
async def leaderboard(user=Depends(current_user)):
    if user["role"] == "ADMIN":
        return {"rankings": app_state.admin_live, "frozen": app_state.leaderboard_frozen}
    return {"rankings": app_state.leaderboard_cache, "frozen": app_state.leaderboard_frozen}
