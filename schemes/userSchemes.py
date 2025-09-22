from pydantic import BaseModel,EmailStr,Field
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class UserRegisterScheme(BaseModel):
    username:EmailStr # account=email
    password:str
    name:Optional[str]=""
    authority:Literal['normal','owner','admin']='normal'
    company:Optional[str]=""
    phone:Optional[str]=""
    role:Optional[str]="" # 角色 
    token:Optional[str]=None # permittion to create a admin account
    note:Optional[str]=""
    department:Optional[list[str]] = Field(default_factory=list)
    
class UserRegisterPasswordPresetScheme(BaseModel):
    username:EmailStr # account=email
    password:str = ""
    name:Optional[str] = ""
    authority:Literal['normal','owner','admin']='normal'
    company:Optional[str]=""
    phone:Optional[str]=""
    role:Optional[str]="" # 角色 
    token:Optional[str]=None # permittion to create a admin account
    note:Optional[str]=""
    department:Optional[list[str]] = ""
    
class UserLoginScheme(BaseModel):
    username:EmailStr # account=email
    password:str

class LoginHistoryRecord(BaseModel):
    username:EmailStr # account=email
    company:str
    authority:Literal['normal','owner','admin']='normal'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class UserFilter(BaseFilter):
    username:Optional[EmailStr]=None # account=email
    name:Optional[str]=None
    authority:Literal['normal','owner','admin']=None
    company:Optional[str]=None
    phone:Optional[str]=None
    role:Optional[str]=None # 角色 
    token:Optional[str]=None # permittion to create a admin account
    note:Optional[str]=None
    department:Optional[list[str]] = None
    
class LoginHistoryFilter(BaseFilter):
    username:EmailStr =None
    company:str =None
    authority:Literal['normal','owner','admin'] = None