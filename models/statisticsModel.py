from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model,auto_build_mongo_filter
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse,KnowledgeHistoryFilter
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme,UserFilter
from tools import trace

class Statistic():
    def __init__(self,request:Request):
        self.db = request.app.state.db
        self.collection = self.db.companies
        self.request=request
    @trace
    async def get_company_employee_count(self,company_id:str):
        return ic(await self.db.user.count_documents({'company':company_id}))
    @trace
    async def get_knowledge_count(self,company_id:str,filter:KnowledgeFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(KnowledgeFilter,filter_dict)
        ic(processed_filter)
        return ic(await self.db.knowledge.count_documents(processed_filter))
    @trace
    async def get_active_user_count(self,company_id:str,filter:UserLoginScheme):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(UserLoginScheme,filter_dict)
        ic(processed_filter)
        return ic(await self.db.login_history.count_documents(processed_filter))
    @trace
    async def get_user_count(self,company_id:str,filter:UserFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(UserFilter,filter_dict)
        ic(processed_filter)
        return ic(await self.db.user.count_documents(processed_filter))
    
    @trace
    async def count_knowledge_history(self,company_id:str,filter:KnowledgeHistoryFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        processed_filter= auto_build_mongo_filter(KnowledgeHistoryFilter,filter_dict)
        processed_filter.update({'company':company_id,"type":"chat"})
        pipeline = [
            {
                "$match": {**processed_filter,
             "linked_knowledge_id": {"$nin": [None, "-1", ""]}
            }},
            {"$group": {
                "_id": "$linked_knowledge_id",     # 根據 linked_knowledge_id 分組
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}               # 出現次數多的在前面
        ]

        ic(pipeline)
        result = await self.db.chat_history.aggregate(pipeline).to_list(length=None)
        return result
    
    
    