from fastapi import FastAPI, HTTPException, Request
from icecream import ic
from bson import ObjectId
from datetime import datetime, timezone

from errors import SettingsError,BadInputError
from tools import _ensure_model,trace,auto_build_mongo_filter
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter,KnowledgeSchemeSolve,KnowledgeSchemeEdit,AggrestionKnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme
from .settingsModel import Settings


class KnowledgeBase():
    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.settings
        self.knowledge = db.knowledge
        self.company = ""
        self.request=request
        
        if 'login' in self.request.session:
            self.company=self.request.session['login'].get('company','')
            ic(self.company)
            if self.company=='':
                raise SettingsError("No Company data")
        else:
            
            raise SettingsError("Not logged in")
    @trace
    async def create_knowledge(self,data:KnowledgeSchemeCreate,display=False):
        from .aiModel import AI
        if len(data.embedding_example_question)==0:
            data.embedding_example_question=await AI(self.request).embedding(data.example_question)
        ic('embedding')
        
        dumped_data=data.model_dump()
        if display:
            ic(dumped_data)
        
        result=await self.knowledge.insert_one(data.model_dump())
        return result.inserted_id
    @trace
    async def get_maincategory(self,filtered_status=False):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        if filtered_status:
            result_list=[]
            for i in result['category']:
                ic(result['category'][i]['status'])
                ic(bool(result['category'][i]['status']))
                if result['category'][i]['status']:
                    result_list.append(i)
            return result_list
        else:
            return list(result['category'].keys())
    @trace
    async def get_subcategory(self,main_category:str):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        for i in result['category']:
            if i==main_category:
                return result['category'][i]['sub']
        return []
    @trace
    async def add_subcategory(self,main_category:str,sub_category:str):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        if main_category not in result['category']:
            raise BadInputError("main_category not exist")

        for i in result['category']:
            if i==main_category:
                if sub_category in result['category'][i]['sub']:
                    return 'already exists'
                
                result['category'][i]['sub'].append(sub_category)
        result = await current_settings.update_settings({"category":result['category']})
    @trace
    async def create_maincategory(self,data:MainCategoriesCreate):
        current_settings=Settings(self.request)
        doc=await current_settings.get_settings()
        
        result = await current_settings.update_settings({"category":data.model_dump(exclude="company_description",by_alias=True)})
        return result
    
    #bug
    @trace
    async def edit_maincategory(self,data:MainCategoriesUpdateScheme):
        current_settings=Settings(self.request)
        result = await current_settings.update_settings({"category":data.model_dump(exclude_none=True,exclude_unset=True)})
        return result
    @trace
    async def reset_maincategory(self):
        template_data=MainCategoriesTemplate().model_dump(by_alias=True,exclude="company_description")
        return await Settings(self.request).update_settings({"category":template_data})
        
    @trace
    async def dispense_department(self,data:DispenseDepartment):
        data_dict=data.model_dump(exclude_none=True,by_alias=True)
        ic(data_dict)
        setting_obj=Settings(self.request)
        setting=await setting_obj.get_settings()
        for i in data_dict:
            if i not in setting['category']:
                raise BadInputError("category 不存在")
            
            if setting['category'][i]['status']:
                setting['category'][i]['access']=data_dict[i]
            else:
                ic(i)
                ic(setting['category'][i]['status'])
        return await setting_obj.update_settings(setting)
    @trace
    async def get_knowledge(self,filter:KnowledgeFilter| AggrestionKnowledgeFilter,include_embedding=False,mask={},time_field="time_stamp_last_edit")->list:
        ic(filter)
        # custome time field 
        if filter.time_field:
            time_field=filter.time_field
            
        filter_dict = filter.model_dump(exclude_none=True,exclude_unset=True)
        
        ic(filter_dict)
        
        mongo_filter = {
            "company": self.company  # 強制篩選公司資料
        }
        
        if "id" in filter_dict:
            try:
                ic('yes')
                if isinstance(filter_dict['id'],list):
                    ids=[]
                    for i in filter_dict['id']:
                        ids.append(ObjectId(i))
                    mongo_filter["_id"]={"$in":ids}
                else:
                    mongo_filter["_id"]=ObjectId(filter_dict['id'])
            except:
                raise BadInputError("id format error")
        
        for field in ["main_category", "sub_category", "created_by",'keywords','status']:
            if field in filter_dict:
                value = filter_dict[field]
                if isinstance(value, list):
                    mongo_filter[field] = {"$in": value}
                else:
                    mongo_filter[field] = value

        # $in可以用來搜索交集
        if "department" in filter_dict:
            mongo_filter["department"] = {"$in": filter_dict["department"]}

        if "start_time" in filter_dict or "end_time" in filter_dict:
            time_filter = {}
            if "start_time" in filter_dict:
                time_filter["$gte"] = filter_dict["start_time"]
            if "end_time" in filter_dict:
                time_filter["$lte"] = filter_dict["end_time"]
            mongo_filter[time_field] = time_filter

        if "keyword" in filter_dict:
            mongo_filter["example_question"] = {
                "$regex": filter_dict["content"],
                "$options": "i"  # 忽略大小寫
            }
    
        # for page saperate
        start_index = filter_dict.get("start_index", 0)
        
        ic(mongo_filter)
        
        if include_embedding:
            cursor = self.knowledge.find(mongo_filter).skip(start_index)
        else:
            cursor = self.knowledge.find(mongo_filter,projection={"embedding_example_question": 0}).skip(start_index)
        
        if mask:
            cursor = self.knowledge.find(mongo_filter,projection=mask).skip(start_index)
        
        if 'limit' in filter_dict:
            limit = filter_dict.get("limit",0)
            if filter_dict['limit']:
                cursor.limit(limit)
    
        #generate final result
        result = await cursor.to_list()
        return result
    
    @trace
    async def delete_knowledge(self,knowledge_id):
        knowledge_id=ObjectId(knowledge_id)
        return await self.knowledge.delete_many({"_id":knowledge_id})
    @trace
    async def solve_knowledge(self,filter:KnowledgeFilter,data:KnowledgeSchemeSolve):
        mongofilter=auto_build_mongo_filter(KnowledgeFilter,filter.model_dump(exclude_unset=True,exclude_defaults=True,exclude=None))
        ic(mongofilter)
        data.status="solved"
        data.time_stamp_last_edit= datetime.now(timezone.utc)
        data_dump=data.model_dump(exclude_unset=True,exclude_defaults=True,exclude=None)
        result = await self.knowledge.update_one(mongofilter,{"$set":data_dump,"$inc":{"edit_count":1}})
        return {"matched":result.matched_count,"modified":result.modified_count}
    
    @trace
    async def edit_knowledge(self,filter:KnowledgeFilter,data:KnowledgeSchemeEdit):
        mongofilter=auto_build_mongo_filter(KnowledgeFilter,filter.model_dump(exclude_unset=True,exclude_defaults=True,exclude=None))
        ic(mongofilter)
        from .aiModel import AI
        
        data.time_stamp_last_edit= datetime.now(timezone.utc)
        # use $inc to increase the field number by specific valule
        if data.example_question:
            data.embedding_example_question=await AI(self.request).embedding(data.example_question)
        ic('embedding')
        result = await self.knowledge.update_one(mongofilter,{"$set":data.model_dump(exclude_unset=True,exclude_defaults=True,exclude=None),"$inc":{"edit_count":1}})
        return {"matched":result.matched_count,"modified":result.modified_count}