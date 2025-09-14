from fastapi import APIRouter,Request,Depends

from schemes.userSchemes import UserLoginScheme,UserRegisterScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models import User
from auth import login_required

router = APIRouter( tags=['User'])

@router.post("/login",response_model=ResponseModel)
async def login(user:UserLoginScheme,request:Request):
    result=await User(request).login(user)
    return ResponseModel(message=result)

@router.post("/logout",response_model=ResponseModel)
async def logout(request:Request):
    result=await User(request).logout()
    return ResponseModel(message=result)

@router.post("/register",response_model=ResponseModel)
async def register(user:UserRegisterScheme,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    result=await User(request).register(user)
    return ResponseModel(message=str(result))

@router.get("/check",response_model=ResponseModel)
async def check(request:Request):
    if 'login' in request.session:
        print(request.session['login'])
        return ResponseModel(message=str(request.session['login']))
    else:
        print("no")
        raise CustomHTTPException(status_code=401,message='Not Logged In')

@router.get("/checkauth",response_model=ResponseModel)
async def checkauthority(request:Request,user_session=Depends(login_required(authority="admin"))):
    return ResponseModel(message=str(request.session['login']))

