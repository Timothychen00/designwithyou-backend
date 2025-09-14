from pydantic import BaseModel,EmailStr
from typing import Literal,Optional

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
    department:str=""
    
class UserLoginScheme(BaseModel):
    username:EmailStr # account=email
    password:str