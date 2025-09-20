from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model
from bson import ObjectId
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme
from errors import CompanyError


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
        await self.edit_company(company_id, departments.model_dump(exclude_none=True,exclude_unset=True))
        return "ok"
    
    async def get_company_departmentlist(self,company_id:str):
        oid=ObjectId(company_id)
        result = await self.collection.find_one({"_id":oid})
        if not result:
            raise BadInputError("Company not found ")
        
        data=[]
        for i in result['departments']:
            data.append(i['department_name'])
        
        return data
    
    
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
