from fastapi import APIRouter,Request

from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme
from models.knowledgeModel import KnowledgeBase
from models.settingsModel import Settings
from auth import login_required

router = APIRouter( tags=['Settings'])

@router.get("/settings")
async def get_setttings(request:Request):
    result = await Settings(request).get_settings()
    return ResponseModel(message=str(result))

@router.put("/settings")
async def update_settings(request:Request,data:SettingsUpdateScheme):
    result = await Settings(request).update_settings(data)
    return ResponseModel(message=str(result))

