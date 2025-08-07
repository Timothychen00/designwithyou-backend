from motor.motor_asyncio import AsyncIOMotorClient # mongodb driver
from fastapi import FastAPI, HTTPException, Request
from passlib.context import CryptContext
from icecream import ic

import os
from contextlib import asynccontextmanager
from schemes import *

from schemes import CustomHTTPException
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 建立好context之後基本上就只有verify和has可以使用

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時
    # configuring local testing env
    
    connection_string="mongodb+srv://timothychenpc:"+os.environ['DB_PASSWORD']+"@cluster0.usqn9tz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    if os.environ['MODE']=='local':
        connection_string="mongodb://localhost:27017/"

    client = AsyncIOMotorClient(connection_string)
    app.state.db_client = client
    app.state.db = client["main"]
    app.state.user = app.state.db.user

    yield  # 這裡是應用程式運行的階段
    #有yield就可以用內建函數next分次執行函數
    # 關閉時
    client.close()
    
    
class User():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.usercollection = db.user
        self.request=request

    async def login(self, user: UserScheme):# Request本身只是class不是物件

        doc = await self.usercollection.find({"username": user.username}).to_list()
        if len(doc) == 0:
            raise CustomHTTPException(status_code=404, message="account not found")
        if verify_password(user.password, doc[0]['password']):
            print('success')
            return 'success'
        else:
            raise CustomHTTPException(status_code=401, message="password not correct")
        
    
    async def logout(self):
        pass
    
    async def register(self, user:UserScheme):
        doc= await self.usercollection.find({'username':user.username}).to_list()# real action happens when .to_list()
        if len(doc)!=0:
            raise CustomHTTPException(status_code=409,message="account already exists!")# try to create something that already exists
        else:
            result=await self.usercollection.insert_one({"username":user.username,"password":get_password_hash(user.password)})
            ic(result)
            return "ok"
            
    
    async def forget(self):
        pass