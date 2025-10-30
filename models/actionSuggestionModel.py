from fastapi import FastAPI, HTTPException, Request
from icecream import ic
import json
import time
from bson import ObjectId
from datetime import datetime, timezone

from errors import SettingsError,BadInputError,ActionSuggestionError
from tools import _ensure_model,cosine_similarity
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.actionSuggestionSchemes import ActionSuggestionFilter,ActionSuggestionCreate,ActionSuggestionEdit,ActionSuggestionReply
from .userModel import User
from .BusinessStrategy import BusinessStrategy
from tools import auto_build_mongo_filter
from .knowledgeModel import KnowledgeBase
from tools import trace


class ActionSuggestion():

    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.action_suggestion
        self.request=request
        self.user_stamp=None
        
        self.agent=request.app.state.agent
        
        if 'login' in self.request.session:
            self.user_stamp=self.request.session['login']
            if not self.user_stamp:
                raise ActionSuggestionError("Not logged in")
            
            self.company=self.request.session['login'].get('company','')
            ic(self.company)
            if self.company=='':
                raise ActionSuggestionError("No Company data")
        else:
            
            raise ActionSuggestionError("Not logged in")

    @trace
    async def get_action_suggestion(self,data_filter:ActionSuggestionFilter | dict):
        if isinstance(data_filter,dict):
            data_filter=_ensure_model(data_filter,ActionSuggestionFilter)
            
        processed_filter = auto_build_mongo_filter(ActionSuggestionFilter,data_filter.model_dump(exclude_none=True),time_field='deadline_time_stamp')
        processed_filter['company']=self.company
        result = await self.collection.find(processed_filter).to_list()
        return result

    @trace
    async def create_action_suggestion(self,data:ActionSuggestionCreate|dict):
        if isinstance(data,dict):
            data=_ensure_model(data,ActionSuggestionCreate)
        data.company=self.company
        data.assignee=self.user_stamp['username']
        data_dict=data.model_dump()

        result = await self.collection.insert_one(data_dict)
        return str(result.inserted_id)
    
    @trace
    async def edit_action_suggestion(self,data_filter:ActionSuggestionFilter|dict,data:ActionSuggestionEdit | dict):
        if isinstance(data_filter,dict):
            data_filter=_ensure_model(data_filter,ActionSuggestionFilter)
    
        if isinstance(data,dict):
            data=_ensure_model(data,ActionSuggestionEdit)
        data_filter.company=self.company
        ic(data_filter)
        data_filter=auto_build_mongo_filter(ActionSuggestionFilter,data_filter.model_dump(exclude_unset=True))
        ic(data_filter)
        ic(data.model_dump(exclude_defaults=True,exclude_unset=True))
        result = await self.collection.update_one(data_filter,{"$set":data.model_dump(exclude_defaults=True,exclude_unset=True)})
        return {"matched":result.matched_count,"modified":result.modified_count}
            
    
    @trace
    async def delete_action_suggestion(self,data_filter:ActionSuggestionFilter):
        processed_filter = auto_build_mongo_filter(ActionSuggestionFilter,data_filter.model_dump(exclude_none=True))
        processed_filter['company']=self.company
        result = await self.collection.delete_many(processed_filter)
        return {"deleted_count": result.deleted_count}

    @trace 
    async def reply(self,filter:ActionSuggestionFilter,user_content:str):
        result=await self.get_action_suggestion(filter)
        records=result[0]['records']
        temp_record = ActionSuggestionReply(
            username=self.user_stamp['username'],
            authority=self.user_stamp['authority'],
            content=user_content
        )
        
        if not records:
            records=[] 
        
        if result[0]['status']!='adopted' and result[0]['status']!='inprogress':
            raise BadInputError("action status is not adopted!")

        updated_dict={}
        updated_dict['records'] = records
        updated_dict['records'].append(temp_record.model_dump())
        if self.user_stamp['authority']=='admin':
            updated_dict['status']='inprogress'

        reply_result = await self.edit_action_suggestion(filter,updated_dict)
        ic(reply_result)
        return reply_result 
    
    @trace
    async def close(self,filter:ActionSuggestionFilter):
        updated_dict={}
        updated_dict['closed_timestamp']=datetime.now(timezone.utc)
        updated_dict['status']='closed'
        reply_result = await self.edit_action_suggestion(filter,updated_dict)
        ic(reply_result)
        return reply_result 
    
    @trace
    async def adopt(self,data_filter:ActionSuggestionFilter,deadline:datetime):
        result = await ActionSuggestion(self.request).edit_action_suggestion(data_filter,{"status":"adopted","deadline_time_stamp":deadline})
        return result
    
    @trace
    async def unadopt(self,data_filter:ActionSuggestionFilter):
        result = await ActionSuggestion(self.request).edit_action_suggestion(data_filter,{"status":"unadopted"})
        return result
# {
    
#     "datetime":datetime
#     "user":str
#     "authority":str
#     "content":str
# }