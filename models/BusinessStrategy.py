from fastapi import FastAPI, HTTPException, Request
from icecream import ic
import json
import time
from bson import ObjectId

from errors import SettingsError,BadInputError,ActionSuggestionError,BusinessStrategyError
from tools import _ensure_model,cosine_similarity
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse,KnowledgeHistoryFilter
from schemes.actionSuggestionSchemes import ActionSuggestionFilter,ActionSuggestionCreate,ActionSuggestionEdit
from schemes.BusinessStrategySchemes import BusinessStrategyCreate,BusinessStrategyEdit,BusinessStrategyFilter
from schemes.knowledgeBaseSchemes import KnowledgeFilter,AggrestionKnowledgeFilter
from .userModel import User
from .settingsModel import Settings
from .statisticsModel import Statistic
from .aiModel import AI
from tools import auto_build_mongo_filter
from .knowledgeModel import KnowledgeBase
from tools import trace

class BusinessStrategy():

    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.business_strategy
        self.request=request
        self.user_stamp=None
        
        self.agent=request.app.state.agent
        
        if 'login' in self.request.session:
            self.user_stamp=self.request.session['login']
            if not self.user_stamp:
                raise BusinessStrategyError("Not logged in")
            
            self.company=self.request.session['login'].get('company','')
            ic(self.company)
            if self.company=='':
                raise BusinessStrategyError("No Company data")
        else:
            
            raise BusinessStrategyError("Not logged in")

    @trace
    async def get_business_strategy(self,data_filter:BusinessStrategyFilter | dict):
        if isinstance(data_filter,dict):
            data_filter=_ensure_model(data_filter,BusinessStrategyFilter)
            
        processed_filter = auto_build_mongo_filter(BusinessStrategyFilter,data_filter.model_dump(exclude_none=True))
        processed_filter['company']=self.company
        result = await self.collection.find(processed_filter).to_list()
        return result

    @trace
    async def create_business_strategy(self,data:BusinessStrategyCreate|dict):
        if isinstance(data,dict):
            data=_ensure_model(data,BusinessStrategyCreate)
        data.company=self.company
        data_dict=data.model_dump(exclude_defaults=True,exclude_unset=True)
        
        result = await self.collection.insert_one(data_dict)
        return result.inserted_id
    
    @trace
    async def edit_business_strategy(self,data_filter:BusinessStrategyFilter,data:BusinessStrategyEdit | dict):
        if isinstance(data,dict):
            data_filter=_ensure_model(data,BusinessStrategyEdit)
        data_filter.company=self.company

        result = await self.collection.update_one(data_filter,data)
        return {"matched":result.matched_count,"modified":result.modified_count}
            
    
    @trace
    async def delete_business_strategy(self,data_filter:BusinessStrategyFilter):
        processed_filter = auto_build_mongo_filter(BusinessStrategyFilter,data_filter.model_dump(exclude_none=True))
        processed_filter['company']=self.company
        result = await self.collection.delete_many(processed_filter)
        return {"deleted_count": result.deleted_count}

    @trace 
    async def generate_ai_strategy(self,strategy_type:str)->BusinessStrategyCreate:
        result = await self.strategy_selected_questions(strategy_type)
        ic(result)
        current_settings=await Settings(self.request).get_settings()
        readings=str(result[1])
        ic(readings)
        
        #main data
        main_category=result[0]
        current_category=current_settings['category']
        if not result[0] in current_category:
            raise BadInputError("main_category not exist")
        
        department=current_category[result[0]]['access']
        tags=await AI(self.request).auto_tagging([],readings,extend=True,count=4,my_model="gpt-4.1-nano",summary_tag=True)
        ic(main_category)
        ic(department)
        ic(tags)
        # tags=讓ai針對這些knowledge給一個
         
        
    @trace
    async def strategy_selected_questions(self,strategy_type:str)->str:
        knowledge_data_mask={"example_question":1,"example_answer":1,"_id":0,"main_category":1,"main_category":1,"sub_category":1} #只有_id可以這樣使用
        
        if strategy_type =='Operational':
            # 搜尋次數最多
            #aggregate不能直接limit
            result = await Statistic(self.request).count_maincategory_history(self.company,KnowledgeHistoryFilter(),limit=1)
            ic(result)
            target_categorys = list(result.keys())
            ic(target_categorys)
            sorted_samples = await Statistic(self.request).count_knowledge_history(self.company,KnowledgeHistoryFilter(main_category=target_categorys))
            ic(sorted_samples)
            ic(list(sorted_samples.keys()))
            # 有alias的不允許使用原本的名字進行呼叫
            target_docs = await KnowledgeBase(self.request).get_knowledge(AggrestionKnowledgeFilter(_id=list(sorted_samples.keys())),mask=knowledge_data_mask)
            ic(target_docs)
            
            if len(target_categorys)==1:
                target_categorys=target_categorys[0]
            return target_categorys,target_docs
        
        elif strategy_type =="Strategy":
            # 待回覆最多
            # status:'suggest-unsolved'

            
            pass
        
        elif strategy_type =='Innovation':# not tested
            # 優化次數最多
            result = await Statistic(self.request).count_maincategory_history(self.company,KnowledgeHistoryFilter(status="rewrite"),limit=1)
            ic(result)
            target_categorys = list(result.keys())
            ic(target_categorys)
            sorted_samples = await Statistic(self.request).count_knowledge_history(self.company,KnowledgeHistoryFilter(main_category=target_categorys))
            ic(sorted_samples)
            ic(list(sorted_samples.keys()))
            # 有alias的不允許使用原本的名字進行呼叫
            target_docs = await KnowledgeBase(self.request).get_knowledge(AggrestionKnowledgeFilter(_id=list(sorted_samples.keys())),mask=knowledge_data_mask)
            ic(target_docs)
            
            if len(target_categorys)==1:
                target_categorys=target_categorys[0]
            return target_categorys,target_docs
            
    
    
    