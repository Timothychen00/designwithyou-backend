from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model,auto_build_mongo_filter
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme,UserFilter

class Statistic():
    def __init__(self,request:Request):
        self.db = request.app.state.db
        self.collection = self.db.companies
        self.request=request
        
    async def get_company_employee_count(self,company_id:str):
        return ic(await self.db.user.count_documents({'company':company_id}))
    
    async def get_knowledge_count(self,company_id:str,filter:KnowledgeFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(KnowledgeFilter,filter_dict)
        ic(processed_filter)
        return ic(await self.db.knowledge.count_documents(processed_filter))
    
    async def get_active_user_count(self,company_id:str,filter:UserLoginScheme):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(UserLoginScheme,filter_dict)
        ic(processed_filter)
        return ic(await self.db.login_history.count_documents(processed_filter))
        
    async def get_user_count(self,company_id:str,filter:UserFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(UserFilter,filter_dict)
        ic(processed_filter)
        return ic(await self.db.user.count_documents(processed_filter))
    
    
    