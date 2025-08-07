from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import lifespan , User
from schemes import ResponseModel, CustomHTTPException,UserScheme

app = FastAPI(lifespan=lifespan)

@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseModel(
            success=False,
            code=exc.code,
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

@app.post("/login",response_model=ResponseModel)
async def login(user:UserScheme,request:Request):
    result=await User(request).login(user)
    return ResponseModel(message=result)

@app.post("/register",response_model=ResponseModel)
async def register(user:UserScheme,request:Request):# fastapi的endpoint名稱是可以重複的，因為綁定的ref的位置而不是名稱（不像是flask）
    result=await User(request).register(user)
    return ResponseModel(message=result)

@app.post("/check",response_model=ResponseModel)
async def check():
    if 'login' in Request.session:
        print(Request.session['login'])
        return ResponseModel(message=Request.session['login'])
    else:
        print("no")
        raise CustomHTTPException(status_code=401,message='Not Logged In')


@app.post("/api/knowledge_base")
async def create_knowledge_base():
    pass
    return "1"


@app.post("/api/knowledge_base/knowledge")
async def create_knowledge():
    pass
    return "1"