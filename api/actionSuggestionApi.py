from fastapi import APIRouter,Request,Depends

from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.companyModel import Company
from models.actionSuggestionModel import ActionSuggestion
from schemes.actionSuggestionSchemes import ActionSuggestionCreate,ActionSuggestionEdit,ActionSuggestionFilter
from auth import login_required

router = APIRouter( tags=['ActionSuggestion'])

# basic 

@router.get("/api/action_suggestion")
async def get_action_suggestion(request: Request,user_session=Depends(login_required(authority="normal"))):
    result = await ActionSuggestion(request).get_action_suggestion({})
    return ResponseModel(message="ok", data=result)

@router.post('/api/action_suggestion/filter')
async def get_filtered_action_suggestion(request:Request,data_filter:ActionSuggestionFilter,user_session=Depends(login_required(authority="normal"))):
    result = await ActionSuggestion(request).get_action_suggestion(data_filter)
    return ResponseModel(message="ok",data = result)

@router.post('/api/action_suggestion')
async def create_action_suggestion(request:Request,data:ActionSuggestionCreate,user_session=Depends(login_required(authority="normal"))):
    result = await ActionSuggestion(request).create_action_suggestion(data)
    return ResponseModel(message="ok",data = result)

@router.put('/api/action_suggestion')
async def edit_action_suggestion(request:Request,data_filter:ActionSuggestionFilter,data:ActionSuggestionCreate,user_session=Depends(login_required(authority="normal"))):
    result = await ActionSuggestion(request).edit_action_suggestion(data_filter,data)
    return ResponseModel(message="ok",data = result)

@router.delete('/api/action_suggestion')
async def delete_action_suggestion(request:Request,data_filter:ActionSuggestionFilter,user_session=Depends(login_required(authority="normal"))):
    result = await ActionSuggestion(request).delete_action_suggestion(data_filter)
    return ResponseModel(message="ok",data = result)

# advanced
@router.post('/api/action_suggestion/reply')
async def reply(request:Request,data_filter:ActionSuggestionFilter,content:str,user_session=Depends(login_required(authority="admin"))):
    result = await ActionSuggestion(request).reply(data_filter,content)
    return ResponseModel(message="ok",data = result)

#結案
@router.post('/api/action_suggestion/close')
async def close(request:Request,data_filter:ActionSuggestionFilter,user_session=Depends(login_required(authority="owner"))):
    result = await ActionSuggestion(request).close(data_filter)
    return ResponseModel(message="ok",data = result)