from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from models import lifespan, User, Settings
from schemes import ResponseModel, CustomHTTPException, UserLoginScheme, KnowledgeScheme, CompanyScheme, UserRegisterScheme,CompanyStructureSetupScheme
from starlette.middleware.sessions import SessionMiddleware

import os
import asyncio

from auth import login_required
from errors import UserError, SettingsError,CompanyError,BadInputError

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(16).hex())

@app.exception_handler(BadInputError)
@app.exception_handler(UserError)
@app.exception_handler(SettingsError)
@app.exception_handler(CompanyError)
async def domain_exception_handler(request: Request, exc: Exception):
    # domain error → 一律 400
    return JSONResponse(
        status_code=400,
        content=ResponseModel(
            success=False,
            status_code=400,
            message=str(exc),
            data=None
        ).model_dump()
    )
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseModel(
            success=False,
            status_code=exc.status_code,
            message=exc.detail,
            data=exc.data
        ).model_dump()
    )

@app.get("/",response_model=ResponseModel)
async def root():
    db = app.state.db
    user_collection = db.user
    # await user_collection.insert_one({"name": 1})
    return ResponseModel(message=db.name)

# 同步的檢查
@app.get("/healthz")
async def healthz(request: Request):
    cache = request.app.state.cache
    return {
        "ready": cache.ready.is_set(),
        "last_error": cache.last_error,
    }


@app.post("/settings")
async def settings_endpoint(request:Request):
    result = await Settings(request).get_settings()
    return ResponseModel(message=str(result))



# login system

@app.post("/login",response_model=ResponseModel)
async def login(user:UserLoginScheme,request:Request):
    result=await User(request).login(user)
    return ResponseModel(message=result)

@app.post("/logout",response_model=ResponseModel)
async def logout(request:Request):
    result=await User(request).logout()
    return ResponseModel(message=result)

@app.post("/register",response_model=ResponseModel)
async def register(user:UserRegisterScheme,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    result=await User(request).register(user)
    return ResponseModel(message=str(result))

@app.get("/check",response_model=ResponseModel)
async def check(request:Request):
    if 'login' in request.session:
        print(request.session['login'])
        return ResponseModel(message=str(request.session['login']))
    else:
        print("no")
        raise CustomHTTPException(status_code=401,message='Not Logged In')

@app.get("/checkauth",response_model=ResponseModel)
async def checkauthority(request:Request,user_session=Depends(login_required(authority="admin"))):
    return ResponseModel(message=str(request.session['login']))


#CRUD API

@app.get("/api/knowledge_base")
async def get_knowledge_base():
    pass
    return "1"

@app.post("/api/knowledge_base")
async def create_knowledge_base():
    pass
    return "1"


@app.get("/api/{main_category}/knowledge")
async def get_knowledge(main_category:str,knowledge:KnowledgeScheme):
    pass
    return "1"

@app.post("/api/{main_category}/knowledge")
async def create_knowledge(main_category:str):
    pass
    return "1"

@app.put("/api/{main_category}/knowledge")
async def edit_knowledge(main_category:str):
    pass
    return "1"

@app.delete("/api/{main_category}/knowledge")
async def delete_knowledge(main_category:str):
    pass
    return "1"

@app.get("/api/knowledge_base/knowledge")
async def get_knowledge():
    pass
    return "1"

# company
from fastapi import Query, Body
import json
from models import Company

@app.get("/api/company")
async def get_company(request: Request,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    company_id=user_session['company_id']
    company = await svc.get_company(company_id)
    return ResponseModel(message="ok", data=company)

@app.post("/api/company")
async def create_company(request: Request, payload: CompanyScheme = None,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    if not payload:
        username=user_session['username']
        company_id = await svc.create_empty_company(username)
        return ResponseModel(message="empty company created", data={"company_id": company_id})
    else:
        company_id = await svc.create_company(payload)
        return ResponseModel(message="company created", data={"company_id": company_id})
    

@app.put("/api/company")
async def edit_company(request: Request, company_id: str, data: CompanyScheme,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.edit_company(company_id, data)
    return ResponseModel(message="updated", data={"status": result})

@app.delete("/api/company")#記得要改使用者那邊
async def delete_company(request: Request, company_id: str ,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.delete_company(company_id)
    return ResponseModel(message="deleted", data={"status": result})


@app.post("/api/company/setup_company_structure")
async def setup_company_structure(request: Request,company_id: str ,departments:CompanyStructureSetupScheme ):
    svc = Company(request)
    result = await svc.setup_company_structure(company_id,departments)
    return ResponseModel(message="ok", data=result)

@app.get("/api/company/department")#記得要改使用者那邊
async def get_departments(request: Request, company_id: str ,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.get_company_departmentlist(company_id)
    return ResponseModel(message="ok", data=result)



# 留stage api讓前端追蹤註冊的進度到哪裡了