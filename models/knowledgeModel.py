from fastapi import FastAPI, HTTPException, Request
from icecream import ic
from bson import ObjectId

from errors import SettingsError,BadInputError
from tools import _ensure_model
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
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
        
    async def create_knowledge(self,data:KnowledgeSchemeCreate):
        ic(data.model_dump())
        result=await self.knowledge.insert_one(data.model_dump())
        return result.inserted_id
    
    async def get_maincategory(self,filtered_status=False):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        if filtered_status:
            result_list=[]
            for i in result['category']:
                if result['category'][i]['status']:
                    result_list.append(i)
            return result_list
        else:
            return list(result['category'].keys())
    
    async def get_subcategory(self,main_category:str):# Request本身只是class不是物件
        current_settings=Settings(self.request)
        result = await current_settings.get_settings()
        for i in result['category']:
            if i==main_category:
                return result['category'][i]['sub']
        return []
    
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
    
    async def create_maincategory(self,data:MainCategoriesCreate):
        current_settings=Settings(self.request)
        doc=await current_settings.get_settings()
        
        result = await current_settings.update_settings({"category":data.model_dump(exclude="company_description",by_alias=True)})
        return result
    
    #bug
    async def edit_maincategory(self,data:MainCategoriesUpdateScheme):
        current_settings=Settings(self.request)
        result = await current_settings.update_settings({"category":data.model_dump(exclude_none=True,exclude_unset=True)})
        return result
    
    async def reset_maincategory(self):
        template_data=MainCategoriesTemplate().model_dump(by_alias=True,exclude="company_description")
        return await Settings(self.request).update_settings({"category":template_data})
        
    
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
    
    async def get_knowledge(self,filter:KnowledgeFilter):
        filter_dict = filter.model_dump(exclude_none=True,exclude_unset=True)
        
        mongo_filter = {
            "company": self.company  # 強制篩選公司資料
        }
        
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
            mongo_filter["timestamp"] = time_filter

        if "keyword" in filter_dict:
            mongo_filter["example_question"] = {
                "$regex": filter_dict["content"],
                "$options": "i"  # 忽略大小寫
            }
    
        # for page saperate
        start_index = filter_dict.get("start_index", 0)
        cursor = self.knowledge.find(mongo_filter).skip(start_index)
        if 'limit' in filter_dict:
            limit = filter_dict.get("limit",0)
            if filter_dict['limit']:
                cursor.limit(limit)
    
        #generate final result
        result = await cursor.to_list()
        return result
    
    async def delete_knowledge(self,knowledge_id):
        knowledge_id=ObjectId(knowledge_id)
        return await self.knowledge.delete_many({"_id":knowledge_id})
        
    async def solve_knowledge(self):
        pass
    
    async def edit_knowledge(self):
        pass