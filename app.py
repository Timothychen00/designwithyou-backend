from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from icecream import ic
import os
import asyncio

from auth import login_required
from models import lifespan, User, Settings,KnowledgeBase,Chat
from schemes import ResponseModel, CustomHTTPException, UserLoginScheme, KnowledgeSchemeCreate, CompanyScheme, UserRegisterScheme,CompanyStructureSetupScheme,MainCategoriesCreate,DispenseDepartment
from errors import UserError, SettingsError,CompanyError,BadInputError
from api import companyApi,knowledgeBaseApi,userApi


app = FastAPI(lifespan=lifespan)

#模組化
app.include_router(companyApi.router)
app.include_router(knowledgeBaseApi.router)
app.include_router(userApi.router)

app.add_middleware(SessionMiddleware, secret_key=os.urandom(16).hex())

#錯誤處理
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



# company

# 留stage api讓前端追蹤註冊的進度到哪裡了