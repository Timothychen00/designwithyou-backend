from motor.motor_asyncio import AsyncIOMotorClient # mongodb driver
from fastapi import FastAPI, HTTPException, Request
from passlib.context import CryptContext
from icecream import ic
from bson import ObjectId
from openai import AsyncOpenAI

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme
from errors import UserError,SettingsError,CompanyError,BadInputError
from tools import token_generator,_ensure_model

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


class User():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.usercollection = db.user
        self.request=request

    async def login(self, user: UserLoginScheme):# Request本身只是class不是物件

        doc = await self.usercollection.find({"username": user.username}).to_list()
        if len(doc) == 0:
            raise CustomHTTPException(status_code=404, message="account not found")
        if verify_password(user.password, doc[0]['password']):
            print('success')
            self.request.session['login']={
                'username':user.username,
                'authority':doc[0]['authority'],
                "company_id":doc[0]['company'],
            }
            return 'success'
        else:
            raise CustomHTTPException(status_code=401, message="password not correct")
        
    
    async def logout(self):
        self.request.session.clear()
        return "logged out!"
    
    async def register(self, user:UserRegisterScheme):
        doc= await self.usercollection.find({'username':user.username}).to_list()# real action happens when .to_list()
        if len(doc)!=0:
            ic(user.username)
            ic(doc)
            raise CustomHTTPException(status_code=409,message="account already exists!")# try to create something that already exists
        else:
            if user.authority in ('admin', 'owner'):
                
                # 之後看還有沒有需要
                if user.token and os.environ.get("ADMIN_TOKEN") and user.token == os.environ.get("ADMIN_TOKEN"):
                    
                    if not user.company:
                        company_id = await Company(self.request).create_empty_company(created_by=user.username)
                    else:
                        company_id=user.company
                    data = {
                        "username": user.username,
                        "password": get_password_hash(user.password),
                        "authority": user.authority,
                        "name":user.name,
                        "company": company_id,
                        "phone": user.phone,
                        "role": user.role,
                        "note":user.note,
                        "department":user.department
                    }

                    
                    try:
                        result = await self.usercollection.insert_one(data)
                        ic(result)
                        return result.inserted_id
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
                data = {
                        "username": user.username,
                        "password": get_password_hash(user.password),
                        "authority": user.authority,
                        "name":user.name,
                        "company": user.company,
                        "phone": user.phone,
                        "role": user.role,
                        "note":user.note,
                        "department":user.department
                }
                result=await self.usercollection.insert_one(data)
                ic(result)
                return result.inserted_id
    
    async def register_many(self,data:list[UserRegisterScheme]):
        pass
    
    async def forget(self):
        pass
    
    async def get_user(self,filter:dict):
        return await self.usercollection.find_one(filter)
    
    async def delete(self, filter:dict):
        await self.usercollection.delete_many(filter) #delete_many 可以適用一個或是多個
        # 為什麼這裡需要await
    
class Settings():
    def __init__(self,request:Request):# init function 不能是async
        db = request.app.state.db
        self.collection = db.settings
        self.company = ""
        self.data={}
        self.request=request
        
        if 'login' in self.request.session:
            ic('login')
            self.company=self.request.session['login'].get('company_id','')
            ic(self.company)
            if self.company=='':
                raise SettingsError("No Company data")
        else:
            
            raise SettingsError("Not logged in")
        

    async def get_settings(self ):# Request本身只是class不是物件
        print('company',self.company)
        
        result= await self.collection.find({"type":"settings","company":self.company}).to_list()
        if len(result)==0:
            simple_settings={
                "company":self.company,# 創建後直接進行綁定
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
            
    
    async def update_settings(self,data:dict | SettingsUpdateScheme):
        _data_model=_ensure_model(data,SettingsUpdateScheme)
        _data=_data_model.model_dump(exclude_none=True,exclude_unset=True,by_alias=True)
        
        if not _data:
            raise BadInputError("No valid fields provided to update")
    
        await self.collection.update_one({"type":"settings","company":self.company},{"$set":_data})
        return 'ok'

    
class KnowledgeBase():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.settings
        self.knowledge = db.knowledge
        self.company = ""
        self.request=request
        
        if 'login' in self.request.session:
            self.company=self.request.session['login'].get('company_id','')
            ic(self.company)
            if self.company=='':
                raise SettingsError("No Company data")
        else:
            
            raise SettingsError("Not logged in")
        
    async def create_knowledge(self,data:KnowledgeSchemeCreate):
        return await self.knowledge.insert_one(data.model_dump())
        

    async def get_maincategory(self):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        return result
    
    async def create_maincategory(self,data:MainCategoriesCreate):
        current_settings=Settings(self.request)
        doc=await current_settings.get_settings()
        
        result = await current_settings.update_settings({"category":data.model_dump(exclude="company_description",by_alias=True)})
        return result
    
    async def edit_maincategory(self,data:MainCategoriesUpdateScheme):
        current_settings=Settings(self.request)
        result = await current_settings.update_settings({"category":data.model_dump(exclude_none=True,exclude_unset=True)})
        return result
    
    async def reset_maincategory(self):
        template_data=MainCategoriesTemplate().model_dump(by_alias=True,exclude="company_description")
        return await Settings(self.request).update_settings({"category":template_data})
        
    
    async def dispense_department(self,data:DispenseDepartment):
        data_dict=data.model_dump(exclude_none=True,by_alias=True)
        ic(data_dict)
        setting_obj=Settings(self.request)
        setting=await setting_obj.get_settings()
        for i in data_dict:
            if i not in setting['category']:
                raise BadInputError("category 不存在")
            
            if setting['category'][i]['status']:
                setting['category'][i]['access']=data_dict[i]
            else:
                ic(i)
                ic(setting['category'][i]['status'])
        return await setting_obj.update_settings(setting)
    
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
            "company_scale":"",#50~100
            "department_count":"",# 部門數量
            "language":"zh",
            "departments":{}
        }
        result = await self.collection.insert_one(file)
        return str(result.inserted_id)

    async def get_company(self,company_id):# Request本身只是class不是物件
        oid=ObjectId(company_id)
        result = await self.collection.find_one({"_id":oid})
        return result
    
    async def setup_company_structure(self,company_id:str,departments:CompanyStructureSetupScheme):
        # 要補之後針對departments的資料格式進行篩選
        
        # create accoutns
        temp_users=[]
        temp_user_ids=[]
        db_departments = [] #map into db format
        try:
            
            for dep in departments.departments:
                temp_user= UserRegisterScheme( #所有的付值都需要await嗎
                    name=dep.person_in_charge.name,
                    password=token_generator(12),
                    username=dep.person_in_charge.email,
                    company_id=company_id
                )
                
                user_id = await User(self.request).register(temp_user)
                temp_user_ids.append(user_id)
                db_departments.append({
                    "department_name": dep.department_name,
                    "parent_department": dep.parent_department,
                    "role": dep.role,
                    "person_in_charge_id": str(user_id),  # 注意轉成 str，避免 BSON 泄漏到前端
                })

            # send email
            ic(temp_users)
            ic(temp_user_ids)
            
            ic(db_departments)
            
            await self.edit_company(company_id, {"departments": db_departments})
            return "ok"
        except Exception as e:
            for id in temp_user_ids:
                await User(self.request).delete({"_id":id})
            raise CompanyError(str(e))
    
    async def get_company_departmentlist(self,company_id:str):
        oid=ObjectId(company_id)
        result = await self.collection.find_one({"_id":oid})
        if not result:
            raise BadInputError("Company not found ")
        
        return list(result['departments'].keys())
    
    
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
            "company_description":"",
            "company_scale":"",#50~100
            "department_count":0,# 部門數量
            "language":"zh",
            "departments":{}
        }
        result=await self.collection.insert_one(file)
        return str(result.inserted_id)
        
    
    async def edit_company(self, company_id: str, data: dict):
        # Validate ObjectId
        # try:
        oid = ObjectId(company_id)
        # except Exception:
        #     raise CompanyError("invalid company id")

        # Whitelist allowed fields
        allowed_keys = {
            "company_name",
            "company_type",
            "company_unicode",
            "company_property",
            "contact_person",
            "company_scale",
            "company_description",
            "departments"
        }
        # 之後應該要改掉
        if not isinstance(data,dict):
            data=data.model_dump(exclude_unset=True)
        update_data = {k: v for k, v in (data or {}).items() if k in allowed_keys}

        if not update_data:
            raise CompanyError("no valid fields to update")

        result = await self.collection.update_one({"_id": oid}, {"$set": update_data})
        if result.matched_count == 0:
            raise CompanyError("company not found")
        return "ok"
    
    async def delete_company(self, company_id: str):
        """Delete a company document by its string id."""
        # try:
        oid = ObjectId(company_id)
        # except Exception:
        #     raise CompanyError("invalid company id")

        result = await self.collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise CompanyError("company not found")
        return "ok"


class AI():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.chat_history
        self.request=request
        
        self.agent=request.app.state.agent

    async def create_record(self, record_type:str,data:RecordCreate ):
        data.type=record_type
        data=_ensure_model(data,RecordCreate)
        data_dict = data.model_dump()
        return await self.collection.insert_one(data_dict)
    
    async def edit_record(self, data:RecordEdit):
        data=_ensure_model(data,RecordEdit)
        data_dict = data.model_dump(exclude_unset=True,exclude_none=True)
        return await self.collection.update_one({"$set":data_dict})
    
    async def ask_question(self,question,by):
        instructions="""
        
        
        
        
        """
        
        resp = await self.agent.responses.create(
            model="gpt-5-nano-2025-08-07",
            instruction=instructions,
            # gpt-5-nano-2025-08-07
            prompt=question,
        )
        self.create_record("chat",RecordCreate(
            ask=question,
            answer=resp.output.text,
            user=by
        ))
        print(resp.output.text)


class Statistic():
    def __init__(self,request:Request):
        self.db = request.app.state.db
        self.collection = self.db.companies
        self.request=request
        
    async def get_company_employee_count(self,company_id:str):
        return ic(await self.db.user.count_documents({'company':company_id}))
    
    async def get_knowledge_count(self,company_id:str,filter:dict={}):
        search_filter={'company':company_id}
        search_filter.update(filter)
        return ic(await self.db.knowledge.count_documents(search_filter))