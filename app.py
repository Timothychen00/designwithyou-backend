from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from icecream import ic
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from contextlib import asynccontextmanager
# from fastapi_profiler import PyInstrumentProfilerMiddleware
import os
import logging
import time
from dotenv import load_dotenv

from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from errors import UserError, SettingsError,CompanyError,BadInputError,AIError
from api import companyApi,knowledgeBaseApi,userApi,settingsApi,actionSuggestionApi
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
load_dotenv()

origins = [    
    "http://localhost:5500",  # 前端開的網址
    "http://localhost:5173",
    "https://design-test.azurewebsites.net",
    "https://design-test.azurewebsites.net:8181"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時
    # configuring local testing env
    connection_string = "mongodb+srv://timothychenpc:" + os.environ['DB_PASSWORD'] + "@cluster0.usqn9tz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    ic(os.environ['MODE'])
    if os.environ['MODE'] == 'local':
        connection_string = "mongodb://localhost:27017/"
        
        

    # MongoDB Agent 
    client = AsyncIOMotorClient(connection_string)
    app.state.db_client = client
    app.state.db = client["main"]
    app.state.user = app.state.db.user
    # OpenAI Agent
    app.state.agent = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    try:
        yield
    finally:
        client.close()

app = FastAPI(lifespan=lifespan)
    
#模組化
app.include_router(companyApi.router)
app.include_router(knowledgeBaseApi.router)
app.include_router(userApi.router)
app.include_router(settingsApi.router)
app.include_router(actionSuggestionApi.router)

# middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.urandom(16).hex(),
    same_site="none", 
    https_only=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.add_middleware(TracingMiddleware)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()  # 高精度計時器
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    # 加入耗時 header（可選）
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"

    # 自定義 log（可換成你自己的 logger）
    logging.info(f"{request.method} {request.url.path} completed in {process_time:.4f} seconds")

    return response

#錯誤處理
@app.exception_handler(AIError)
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

# 留stage api讓前端追蹤註冊的進度到哪裡了
