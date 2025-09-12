from fastapi import APIRouter,Request

from schemes import ResponseModel
from models import Settings
from auth import login_required

router = APIRouter( tags=['Settings'])

@router.post("/settings")
async def settings_endpoint(request:Request):
    result = await Settings(request).get_settings()
    return ResponseModel(message=str(result))

