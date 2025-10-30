from fastapi import FastAPI, HTTPException, Request
from icecream import ic
from passlib.context import CryptContext
import os

from errors import BadInputError
from tools import _ensure_model,token_generator
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme,LoginHistoryRecord
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme
from .companyModel import Company
from errors import CompanyError,UserError
from tools import trace

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 建立好context之後基本上就只有verify和has可以使用
@trace
def verify_password(plain_password, hashed_password):
    ic(plain_password)
    if not plain_password or not isinstance(plain_password, str):
        raise ValueError("Invalid plain password format (must be str, non-empty)")
    if not hashed_password or not isinstance(hashed_password, str):
        raise ValueError("Invalid hashed password format (must be str)")
    return pwd_context.verify(plain_password, hashed_password)
@trace
def get_password_hash(password):
    hashed=pwd_context.hash(password)
    print(len(hashed))
    return hashed


class User():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.usercollection = db.user
        self.login_history=db.login_history
        self.request=request
    @trace
    async def login(self, user: UserLoginScheme):# Request本身只是class不是物件

        doc = await self.usercollection.find({"username": user.username}).to_list()
        if len(doc) == 0:
            raise CustomHTTPException(status_code=404, message="account not found")
        if verify_password(user.password, doc[0]['password']):
            print('success')
            stamp={
                'username':user.username,
                'authority':doc[0]['authority'],
                "company":doc[0]['company'],
            }
            self.request.session['login']=stamp
            
            await self.save_login_record(stamp)
            return 'success'
        else:
            raise CustomHTTPException(status_code=401, message="password not correct")
        
    @trace
    async def logout(self):
        self.request.session.clear()
        return "logged out!"
    @trace
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
    @trace
    async def register_many(self,token,company_id:str,userdata:list[UserRegisterPasswordPresetScheme]):
        # 要補之後針對departments的資料格式進行篩選
        
        # create accoutnsa
        temp_users=[]
        temp_user_ids=[]
        departments= await Company(self.request).get_company_departmentlist(company_id)
        try:
            
            for user in userdata:
                user.company=company_id
                user.password=token_generator(12)# 隨機產生密碼
                
                not_department=0
                for i in user.department:
                    if i not in departments:
                        not_department+=1
                    
                ic(not_department)
                if not_department:
                    raise BadInputError("User Department data error, please check and try again.")
                
                
                user.token=token
                user_id = await User(self.request).register(user)
                temp_user_ids.append(user_id)

            # send email
            ic(temp_users)
            ic(temp_user_ids)
            return "ok"
        except Exception as e:
            for id in temp_user_ids:
                await User(self.request).delete({"_id":id})
            raise
    @trace
    async def forget(self):
        pass
    @trace
    async def get_user(self,filter:dict,company_id:str=""):
        if not filter:
            filter={}
        if company_id:
            filter['company']=company_id
        return await self.usercollection.find_one(filter)
    
    @trace
    async def get_users(self,filter:dict,company_id:str=""):
        if not filter:
            filter={}
        if company_id:
            filter['company']=company_id
        return await self.usercollection.find(filter).to_list()
    
    @trace
    async def delete(self, filter:dict):
        return await self.usercollection.delete_many(filter) #delete_many 可以適用一個或是多個
        # 為什麼這裡需要await
    @trace
    async def save_login_record(self,user:LoginHistoryRecord):
        data=_ensure_model(user,LoginHistoryRecord)
        data_dump=data.model_dump()
        ic(data_dump)
        
        result=await self.login_history.insert_one(data_dump)
        return result.inserted_id
    
