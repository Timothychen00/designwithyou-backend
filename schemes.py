from fastapi import HTTPException

from typing import Any, Optional, Literal
from pydantic import BaseModel,EmailStr, field_serializer

from tools import bson_to_jsonable

class UserRegisterScheme(BaseModel):
    username:EmailStr # account=email
    password:str
    name:Optional[str]=""
    authority:Literal['normal','owner','admin']
    company:Optional[str]=""
    phone:Optional[str]=""
    role:Optional[str]="" # 角色 
    token:Optional[str]=None # permittion to create a admin account
    note:Optional[str]=""
    
class UserLoginScheme(BaseModel):
    username:EmailStr # account=email
    password:str
    

class KnowledgeScheme(BaseModel):
    _id:str
    department:str
    example_question:str
    example_answer:str
    
    main_category:str
    sub_category:str
    tag:list[str]
    keywords:list[str]
    files:list[str]
    status:Literal['solved','unsolved'] #是否被解決
    report:str #?
    timestamp:str
    
class ContactPerson(BaseModel):
    name: str
    email: EmailStr
    phone: str
    
class MainCategoryConfig(BaseModel):
    description: list[str]
    sub: list[str]
    access: list[str]

class MainCategories(BaseModel):
    # 僅這些 key 合法；沒出現在這裡的 key 會被直接擋掉
    品質管理: Optional[MainCategoryConfig] = None
    倉儲管理: Optional[MainCategoryConfig] = None
    生產管理: Optional[MainCategoryConfig] = None
    客戶服務: Optional[MainCategoryConfig] = None
    採購管理: Optional[MainCategoryConfig] = None
    設備維護: Optional[MainCategoryConfig] = None
    能源管理: Optional[MainCategoryConfig] = None
    物流與配送: Optional[MainCategoryConfig] = None
    研發與創新: Optional[MainCategoryConfig] = None
    財務管理: Optional[MainCategoryConfig] = None
    人力資源: Optional[MainCategoryConfig] = None
    數據安全與治理: Optional[MainCategoryConfig] = None
    
    
class CompanyScheme(BaseModel):
    company_name: str
    company_type: str
    company_unicode: str  # 統編
    company_property: list[str]
    contact_person: ContactPerson
    company_description: Optional[str] = ""
    company_scale:str="",#50~100
    department_count:int
    language:str="zh"

# Response Scheme

#定義標準的回應格式
class ResponseModel(BaseModel):
    success: bool = True
    status_code: int = 200 
    message: str # 提示訊息
    data: Optional[Any] = None #如果需要夾帶資料的話可以放這裡

    @field_serializer('data') # 針對data這個欄位進行客製化的serialize，解決bson會出現的問題
    def serialize_data(self, v):
        return bson_to_jsonable(v)  # 低迴進行控制

# 在原本HTTPException的基礎上加入data和code欄位
class CustomHTTPException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        # super()本身只會拿到父物件，如果需要call 父親物件的constructor需要手動另外呼叫
        super().__init__(status_code=status_code, detail=message)
        self.data = data
        
