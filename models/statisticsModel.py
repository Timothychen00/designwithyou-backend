from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme

class Statistic():
    def __init__(self,request:Request):
        self.db = request.app.state.db
        self.collection = self.db.companies
        self.request=request
        
    async def get_company_employee_count(self,company_id:str):
        return ic(await self.db.user.count_documents({'company':company_id}))
    
    async def get_knowledge_count(self,company_id:str,filter:dict={}):
        filter.update({'company':company_id})
        return ic(await self.db.knowledge.count_documents(filter))