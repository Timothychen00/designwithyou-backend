from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from models import lifespan , User
from schemes import ResponseModel, CustomHTTPException,UserScheme, KnowledgeScheme
from starlette.middleware.sessions import SessionMiddleware

import os

from auth import login_required

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(16).hex())

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
    db= app.state.db
    user_collection=db.user
    user_collection.insert_one({"name":1})
    return  ResponseModel(message=db.name)

# login system

@app.post("/login",response_model=ResponseModel)
async def login(user:UserScheme,request:Request):
    result=await User(request).login(user)
    return ResponseModel(message=result)

@app.post("/logout",response_model=ResponseModel)
async def logout(request:Request):
    result=await User(request).logout()
    return ResponseModel(message=result)

@app.post("/register",response_model=ResponseModel)
async def register(user:UserScheme,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    result=await User(request).register(user)
    return ResponseModel(message=result)

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