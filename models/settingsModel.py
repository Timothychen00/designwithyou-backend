from fastapi import FastAPI, HTTPException, Request
from icecream import ic

from errors import SettingsError,BadInputError
from tools import _ensure_model
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from schemes.settingsSchemes import SettingsUpdateScheme


class Settings():
    def __init__(self,request:Request):# init function 不能是async
        db = request.app.state.db
        self.collection = db.settings
        self.company = ""
        self.data={}
        self.request=request
        
        if 'login' in self.request.session:
            ic('login')
            self.company=self.request.session['login'].get('company','')
            ic(self.company)
            if self.company=='':
                raise SettingsError("No Company data")
        else:
            
            raise SettingsError("Not logged in")
        

    async def get_settings(self ):# Request本身只是class不是物件
        print('company',self.company)
        
        result= await self.collection.find({"type":"settings","company":self.company}).to_list()
        if len(result)==0:
            simple_settings={
                "company":self.company,# 創建後直接進行綁定
                "type":"settings",
                "category":{
                }
                }
            await self.collection.insert_one(simple_settings)
            self.data=simple_settings
            return simple_settings
        else:
            self.data=result[0]
            return result[0]
            
    
    async def update_settings(self,data:dict | SettingsUpdateScheme):
        _data_model=_ensure_model(data,SettingsUpdateScheme)
        _data=_data_model.model_dump(exclude_none=True,exclude_unset=True,by_alias=True)
        
        if not _data:
            raise BadInputError("No valid fields provided to update")
    
        await self.collection.update_one({"type":"settings","company":self.company},{"$set":_data})
        return 'ok'