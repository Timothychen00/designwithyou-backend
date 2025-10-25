from fastapi import APIRouter,Request,Depends
from typing import Literal

from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.companyModel import Company
from models.BusinessStrategy import BusinessStrategy
from schemes.BusinessStrategySchemes import BusinessStrategyCreate,BusinessStrategyEdit,BusinessStrategyFilter
from auth import login_required
from tools import trace

router = APIRouter( tags=['BusinessStrategy'])
# basic 
@trace
@router.get("/api/business_strategy")
async def get_business_strategy(request: Request,user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).get_business_strategy({})
    return ResponseModel(message="ok", data=result)

@trace
@router.post('/api/business_strategy/filter')
async def get_filtered_business_strategy(request:Request,data_filter:BusinessStrategyFilter,user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).get_business_strategy(data_filter)
    if len(result)==0:
        if user_session['authority']=='owner':
            result = await BusinessStrategy(request).generate_ai_strategy(data_filter.type)
    return ResponseModel(message="ok",data = result)

@trace
@router.post('/api/business_strategy')
async def create_business_strategy(request:Request,data:BusinessStrategyCreate,user_session=Depends(login_required(authority="normal"))):
    result = await BusinessStrategy(request).create_business_strategy(data)
    return ResponseModel(message="ok",data = result)

@trace
@router.put('/api/business_strategy')
async def edit_business_strategy(request:Request,data_filter:BusinessStrategyFilter,data:BusinessStrategyEdit,user_session=Depends(login_required(authority="normal"))):
    result = await BusinessStrategy(request).edit_business_strategy(data_filter,data)
    return ResponseModel(message="ok",data = result)

@trace
@router.delete('/api/business_strategy')
async def delete_business_strategy(request:Request,data_filter:BusinessStrategyFilter,user_session=Depends(login_required(authority="normal"))):
    result = await BusinessStrategy(request).delete_business_strategy(data_filter)
    return ResponseModel(message="ok",data = result)

# advanced
@trace
@router.post('/api/business_strategy/generate')
async def generate(request:Request,data_filter:Literal['Operational',"Strategy",'Innovation'],user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).generate_ai_strategy(data_filter)
    return ResponseModel(message="ok",data = result)

@trace
@router.post('/api/business_strategy/adopt')
async def adopt(request:Request,data_filter:Literal['Operational',"Strategy",'Innovation'],user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).adopt(data_filter)
    return ResponseModel(message="ok",data = result)

@trace
@router.post('/api/business_strategy/unadopt')
async def unadopt(request:Request,data_filter:Literal['Operational',"Strategy",'Innovation'],user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).unadopt(data_filter)
    return ResponseModel(message="ok",data = result)

@trace
@router.post('/api/business_strategy/generate_brief')
async def generate_brief(request:Request,user_session=Depends(login_required(authority="admin"))):
    result = await BusinessStrategy(request).generate_ai_strategy_brief()
    return ResponseModel(message="ok",data = result)

