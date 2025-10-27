from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model,auto_build_mongo_filter
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse,KnowledgeHistoryFilter,KnowledgeHistoryGroup
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter,GroupKnowledgeFilter
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
    async def get_knowledge_count(self,company_id:str,filter:KnowledgeFilter | dict):
        if isinstance(filter,dict):
            filter=_ensure_model(filter,KnowledgeFilter)
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(KnowledgeFilter,filter_dict,time_field=filter.time_field)
        ic(processed_filter)
        
        return ic(await self.db.knowledge.count_documents(processed_filter))
    
    @trace
    async def group_knowledge_count(self,company_id:str,filter:KnowledgeFilter | dict,group:GroupKnowledgeFilter,limit=None):
        if isinstance(filter,dict):
            filter=_ensure_model(filter,KnowledgeFilter)
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        filter_dict.update({'company':company_id})
        processed_filter= auto_build_mongo_filter(KnowledgeFilter,filter_dict)
        
        pipeline=[
            {"$match": processed_filter},
            {"$group": {"_id": "$username"}},
            {"$count": "distinct_users"}
        ]
        composed_id={
        }
        
        # add grouping support
        if group:
            dumped=group.model_dump(exclude_defaults=True,exclude_unset=True)
            ic(dumped)
            for i in dumped:
                if dumped[i]:
                    composed_id[i]=f"${i}"
        ic(composed_id)
        
        pipeline = [
            {"$match": processed_filter},
            {"$group": {
                "_id": composed_id,    
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}               # 出現次數多的在前面
        ]
        
        if limit:
            pipeline.append({"$limit":limit})
        ic(pipeline)
        
        result = await self.db.knowledge.aggregate(pipeline).to_list(length=None)
        ic(result)
        
        return result
    @trace
    async def get_active_user_count(self,company_id:str,filter:UserLoginScheme):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        
        processed_filter= auto_build_mongo_filter(UserLoginScheme,filter_dict)
        processed_filter.update({'company':company_id})
        ic(processed_filter)
        
        pipeline = [
            {"$match": processed_filter},
            {"$group": {"_id": "$username"}},
            {"$count": "distinct_users"}
        ]
        
        # distinct_user 是用來規定回傳的result的長相
        result = await self.db.login_history.aggregate(pipeline).to_list(length=1)
        return result[0]["distinct_users"] if result else 0
        
    @trace
    async def get_user_count(self,company_id:str,filter:UserFilter):
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        
        processed_filter= auto_build_mongo_filter(UserFilter,filter_dict)
        processed_filter.update({'company':company_id})
        ic(processed_filter)
        return ic(await self.db.user.count_documents(processed_filter))
    
    @trace
    async def count_knowledge_history(self,company_id:str,filter:KnowledgeHistoryFilter|dict,limit=None,grouping:KnowledgeHistoryGroup=None):
        if isinstance(filter,dict):
            filter=_ensure_model(filter,KnowledgeHistoryFilter)
            
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        processed_filter= auto_build_mongo_filter(KnowledgeHistoryFilter,filter_dict)
        ic(processed_filter)
        processed_filter.update({'company':company_id})
        
        composed_id={
            "knowledge_id":"$linked_knowledge_id",
        }
        # add grouping support
        if grouping:
            dumped=grouping.model_dump()
            for i in dumped:
                if dumped[i]:
                    composed_id[i]=f"${i}"
        ic(composed_id)
        
        pipeline = [
            {
                "$match": {**processed_filter,
                "linked_knowledge_id": {"$nin": [None, "-1", ""]}
            }},
            {"$group": {
                "_id": composed_id,     # 根據 linked_knowledge_id 分組
                "count": {"$sum": 1}
            }},
            
            {"$sort": {"count": -1}}               # 出現次數多的在前面
        ]
        
        if limit:
            pipeline.append({"$limit":limit})
        ic(pipeline)
        
        result = await self.db.chat_history.aggregate(pipeline).to_list(length=None)
        ic(result)
        
        # processed_result={}
        # for i in result:
        #     processed_result[i['_id']['knowledge_id']]=i['count']
        # ic(processed_result)
        
        return result
    
    @trace
    async def group_knowledge_history(self,company_id:str,filter:KnowledgeHistoryFilter|dict,limit=None,grouping:KnowledgeHistoryGroup=None):
        if isinstance(filter,dict):
            filter=_ensure_model(filter,KnowledgeHistoryFilter)
            
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        processed_filter= auto_build_mongo_filter(KnowledgeHistoryFilter,filter_dict)
        ic(processed_filter)
        processed_filter.update({'company':company_id})
        
        composed_id={
        }
        # add grouping support
        if grouping:
            dumped=grouping.model_dump()
            for i in dumped:
                if dumped[i]:
                    composed_id[i]=f"${i}"
        ic(composed_id)
        
        pipeline = [
            {
                "$match": {**processed_filter
            }},
            {"$group": {
                "_id": composed_id,     # 根據 linked_knowledge_id 分組
                "count": {"$sum": 1}
            }},
            
            {"$sort": {"count": -1}}               # 出現次數多的在前面
        ]
        
        if limit:
            pipeline.append({"$limit":limit})
        ic(pipeline)
        
        result = await self.db.chat_history.aggregate(pipeline).to_list(length=None)
        ic(result)
        
        return result
    
    @trace
    async def count_maincategory_history(self,company_id:str,filter:KnowledgeHistoryFilter|dict,limit=None):
        if isinstance(filter,dict):
            filter=_ensure_model(filter,KnowledgeHistoryFilter)
            
        filter_dict=filter.model_dump(exclude_none=True,exclude_unset=True)
        processed_filter= auto_build_mongo_filter(KnowledgeHistoryFilter,filter_dict)
        processed_filter.update({'company':company_id})
        pipeline = [
            {
                "$match": {**processed_filter,
                "main_category": {"$nin": [None, "-1", ""]}
            }},
            {"$group": {
                "_id": "$main_category",     # 分組
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}               # 出現次數多的在前面
        ]

        if limit:
            pipeline.append({"$limit":limit})
            
        ic(pipeline)
        result = await self.db.chat_history.aggregate(pipeline).to_list()
        # for i in result[0]:
        #     i['main_category']=i["_id"]
        #     ]
        ic(result)
        processed_result={}
        for i in result:
            processed_result[i['_id']]=i['count']
        return processed_result
    
    