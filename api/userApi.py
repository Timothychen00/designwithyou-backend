from fastapi import APIRouter,Request,Depends,Query
from typing import Literal

from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.userModel import User
from auth import login_required
from models.statisticsModel import Statistic
from schemes.userSchemes import UserFilter,LoginHistoryFilter,LoginHistoryFilterTimeGroup
from tools import trace

router = APIRouter(prefix="/api/user",tags=['User'])


@trace
@router.post("/login",response_model=ResponseModel)
async def login(user:UserLoginScheme,request:Request):
    result=await User(request).login(user)
    return ResponseModel(message=result)

@trace
@router.post("/logout",response_model=ResponseModel)
async def logout(request:Request):
    result=await User(request).logout()
    return ResponseModel(message=result)

@trace
@router.post("/register",response_model=ResponseModel)
async def register(user:UserRegisterScheme,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    """
        Register a single user
        
        if authority is ["admin","owner"] and the token argument is provided
        then this will automatically create a binding company instance
    """
    result=await User(request).register(user)
    return ResponseModel(message=str(result))

@trace
@router.post("/delete",response_model=ResponseModel)
async def delete_user(username:str,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    result=await User(request).delete({"username":username})
    return ResponseModel(message=str(result))

@trace
@router.post("/register_many",response_model=ResponseModel)
async def register(user:list[UserRegisterPasswordPresetScheme],request:Request,token:str,user_session=Depends(login_required(authority="normal"))):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    """
        for Step5
        
        Used for auto complete company for creating users (In order to fulfill this, login is required)
    """
    
    company_id=user_session["company"]
    result=await User(request).register_many(token,company_id,user)
    return ResponseModel(message=str(result))

@trace
@router.get("/check",response_model=ResponseModel)
async def check(request:Request):
    if 'login' in request.session:
        print(request.session['login'])
        return ResponseModel(message=str(request.session['login']))
    else:
        print("no")
        raise CustomHTTPException(status_code=401,message='Not Logged In')

@trace
@router.get("/checkauth",response_model=ResponseModel)
async def checkauthority(request:Request,user_session=Depends(login_required(authority="normal"))):
    return ResponseModel(message=str(request.session['login']))

# modified 
@trace
@router.post('/user_count/filter',tags=['Statistics'])
async def get_filtered_user_count(request:Request,filter:UserFilter,active:bool=Query(False),user_session=Depends(login_required(authority="normal"))):
    company_id=user_session['company']
    if active:
        result=await Statistic(request).get_active_user_count(company_id,filter)
    else:
        result=await Statistic(request).get_user_count(company_id,filter)
    return ResponseModel(message="ok", data=result)

@trace
@router.get('/user_count',tags=['Statistics'])
async def get_total_user_count(request:Request,active:bool=Query(False),user_session=Depends(login_required(authority="normal"))):
    company_id=user_session['company']
    if active:
        result=await Statistic(request).get_active_user_count(company_id,UserFilter())
    else:
        result=await Statistic(request).get_user_count(company_id,UserFilter())
    return ResponseModel(message="ok", data=result)


@trace
@router.post('/user_login_analysis',tags=['Statistics'])
async def get_user_login_analysis(request:Request,filter:LoginHistoryFilterTimeGroup,unit:Literal['day','week','month']='day',user_session=Depends(login_required(authority="normal"))):
    company_id=user_session['company']
    result= await Statistic(request).get_user_login_analysis(company_id,filter,unit)
    return ResponseModel(message="ok", data=result)