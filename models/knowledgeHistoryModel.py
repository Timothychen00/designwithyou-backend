from fastapi import FastAPI, HTTPException, Request
from icecream import ic
import json
import time
from bson import ObjectId
from datetime import datetime, timezone

from errors import SettingsError,BadInputError,ActionSuggestionError
from tools import _ensure_model,cosine_similarity
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse,KnowledgeHistoryFilter
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.actionSuggestionSchemes import ActionSuggestionFilter,ActionSuggestionCreate,ActionSuggestionEdit,ActionSuggestionReply
from .userModel import User
from tools import auto_build_mongo_filter
from .knowledgeModel import KnowledgeBase
from tools import trace


class KnowledgeHistory():

    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.chat_history
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
    async def get_knowledge_history(self,data_filter:KnowledgeHistoryFilter | dict):
        if isinstance(data_filter,dict):
            data_filter=_ensure_model(data_filter,KnowledgeHistoryFilter)
            
        processed_filter = auto_build_mongo_filter(KnowledgeHistoryFilter,data_filter.model_dump(exclude_none=True))
        processed_filter['company']=self.company
        mask={
            "prompt":0,
            "status":0,
        }
        result = await self.collection.find(processed_filter,mask).to_list()
        return result

    