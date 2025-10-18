from fastapi import FastAPI, HTTPException, Request
from icecream import ic
import json
import time
from bson import ObjectId

from errors import SettingsError,BadInputError,ActionSuggestionError
from tools import _ensure_model,cosine_similarity
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.actionSuggestionSchemes import ActionSuggestionFilter,ActionSuggestionCreate,ActionSuggestionEdit
from .userModel import User
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
    async def edit_action_suggestion(self,data_filter:ActionSuggestionFilter,data:ActionSuggestionEdit | dict):
        if isinstance(data,dict):
            data_filter=_ensure_model(data,ActionSuggestionEdit)
        data_filter.company=self.company

        result = await self.collection.update_one(data_filter,data)
        return {"matched":result.matched_count,"modified":result.modified_count}
            
    
    @trace
    async def delete_action_suggestion(self,data_filter:ActionSuggestionFilter):
        processed_filter = auto_build_mongo_filter(ActionSuggestionFilter,data_filter.model_dump(exclude_none=True))
        processed_filter['company']=self.company
        result = await self.collection.delete_many(processed_filter)
        return {"deleted_count": result.deleted_count}
