from fastapi import HTTPException

from typing import Any, Optional, Literal
from pydantic import BaseModel,EmailStr

class UserScheme(BaseModel):
    username:str
    password:str
    authority:Literal['normal','owner','admin']
    company:Optional[str]=""
    token:Optional[str]=None # permittion to create a admin account

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
    
class CompanyScheme(BaseModel):
    company_name: str
    company_type: str
    company_unicode: str  # 統編
    company_property: list[str]
    contact_person: ContactPerson
    company_description: Optional[str] = ""

# Response Scheme

#定義標準的回應格式
class ResponseModel(BaseModel):
    success: bool = True
    status_code: int = 200 
    message: str # 提示訊息
    data: Optional[Any] = None #如果需要夾帶資料的話可以放這裡


# 在原本HTTPException的基礎上加入data和code欄位
class CustomHTTPException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        # super()本身只會拿到父物件，如果需要call 父親物件的constructor需要手動另外呼叫
        super().__init__(status_code=status_code, detail=message)
        self.data = data