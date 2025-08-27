from motor.motor_asyncio import AsyncIOMotorClient # mongodb driver
from fastapi import FastAPI, HTTPException, Request
from passlib.context import CryptContext
from icecream import ic
from bson import ObjectId

import os
import asyncio
import anyio    #async corotine的lock
from contextlib import asynccontextmanager
from schemes import *

from schemes import CustomHTTPException
from errors import UserError,SettingsError,CompanyError
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
    connection_string = "mongodb+srv://timothychenpc:" + os.environ['DB_PASSWORD'] + "@cluster0.usqn9tz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    if os.environ['MODE'] == 'local':
        connection_string = "mongodb://localhost:27017/"

    client = AsyncIOMotorClient(connection_string)
    app.state.db_client = client
    app.state.db = client["main"]
    app.state.user = app.state.db.user
    
    try:
        yield
    finally:
        client.close()

app = FastAPI(lifespan=lifespan)



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
            self.request.session['login']={
                'username':user.username,
                'authority':doc[0]['authority']
            }
            return 'success'
        else:
            raise CustomHTTPException(status_code=401, message="password not correct")
        
    
    async def logout(self):
        self.request.session.clear()
        return "logged out!"
    
    async def register(self, user:UserScheme):
        doc= await self.usercollection.find({'username':user.username}).to_list()# real action happens when .to_list()
        if len(doc)!=0:
            raise CustomHTTPException(status_code=409,message="account already exists!")# try to create something that already exists
        else:
            if user.authority in ('admin', 'owner'):
                if user.token and os.environ.get("ADMIN_TOKEN") and user.token == os.environ.get("ADMIN_TOKEN"):

                    company_id = await Company(self.request).create_empty_company(created_by=user.username)

                    data = {
                        "username": user.username,
                        "password": get_password_hash(user.password),
                        "authority": user.authority,
                        "company": company_id,
                    }
                    try:
                        result = await self.usercollection.insert_one(data)
                        ic(result)
                        return "ok"
                    except Exception as e:
                        # compensation: remove the created company to avoid orphaned doc
                        try:
                            await Company(self.request).delete_company(company_id)
                        except Exception:
                            pass
                        raise UserError("failed to create admin user")
                else:
                    raise UserError("permission denied")
            else:
                # normal create
                result=await self.usercollection.insert_one(data)
                ic(result)
                return "ok"
            
    
    async def forget(self):
        pass
    


    
class Settings():
    def __init__(self,request:Request):# init function 不能是async
        db = request.app.state.db
        self.collection = db.settings
        self.company = ""
        self.data={}
        self.request=request
        
        if 'login' in self.request.session:
            self.company=self.request.session.get('company','')
            if self.company=='':
                raise SettingsError("No Company data")
        else:
            
            raise SettingsError("Not logged in")
        

    async def get_settings(self ):# Request本身只是class不是物件
        print('company',self.company)
        
        result= await self.collection.find({"type":"settings","company":self.company}).to_list()
        if len(result)==0:
            simple_settings={
                "company":"",
                "type":"settings",
                "category":{
                }
                }
            await self.collection.insert_one(simple_settings)
            self.data=simple_settings
            return simple_settings
        else:
            self.data=result[0]
            return result[0]
            
    
    async def update_settings(self,data:dict):
        result=await self.collection.update_one({"type":"settings","company":self.company},{"$set":data})
        return result

    
class KnowledgeBase():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.settings
        self.request=request
        self.data_settings=self.request.app.state.data_settings

    async def get_maincategory(self,category:str):# Request本身只是class不是物件
        pass
    
    async def create_maincategory(self,main_category:str,subcategory:str):
        if main_category not in self.data_settings.data['category']:
            self.data_settings.data['category'][main_category]=subcategory
            self.data_settings.update()
            return 'success'
        else:
            raise CustomHTTPException(message="already exist!",status_code=409)
            
        
    
    async def edit_maincategory(self):
        verify_password
    
    async def delete_maincategory(self):
        pass
    
    
class Company():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.companies
        self.request=request

    async def create_empty_company(self, created_by: str):
        file = {
            "company_name": "",
            "company_type": "",
            "company_unicode": "",
            "company_property": [],
            "contact_person": {
                "name": "",
                "email": "",
                "phone": "",
            },
            "company_description": "",
            "created_by": created_by,
            "status": "draft",
        }
        result = await self.collection.insert_one(file)
        return str(result.inserted_id)

    async def get_company(self,):# Request本身只是class不是物件
        pass
    
    async def create_company(self,data:CompanyScheme):
        file={
            "company_name":data.company_name,
            "company_type":data.company_type,
            "company_unicode":data.company_unicode,#統編
            "company_property":data.company_property,
            "contact_person":{
                "name":data.contact_person.name,
                "email":data.contact_person.email,
                "phone":data.contact_person.phone
                },
            "company_description":""
        }
        result=await self.collection.insert_one(file)
        return str(result.inserted_id)
        
    
    async def edit_company(self, company_id: str, data: dict):
        # Validate ObjectId
        try:
            oid = ObjectId(company_id)
        except Exception:
            raise CompanyError("invalid company id")

        # Whitelist allowed fields
        allowed_keys = {
            "company_name",
            "company_type",
            "company_unicode",
            "company_property",
            "contact_person",
            "company_description",
        }
        update_data = {k: v for k, v in (data or {}).items() if k in allowed_keys}
        if not update_data:
            raise CompanyError("no valid fields to update")

        result = await self.collection.update_one({"_id": oid}, {"$set": update_data})
        if result.matched_count == 0:
            raise CompanyError("company not found")
        return "ok"
    
    async def delete_company(self, company_id: str):
        """Delete a company document by its string id."""
        try:
            oid = ObjectId(company_id)
        except Exception:
            raise CompanyError("invalid company id")

        result = await self.collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise CompanyError("company not found")
        return "ok"