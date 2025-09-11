from fastapi import HTTPException

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from typing import Any, Optional, Literal
from pydantic import BaseModel,EmailStr, field_serializer,Field,ConfigDict

from tools import bson_to_jsonable

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

class KnowledgeSchemeCreate(BaseModel):
    _id:str
    department:list[str]
    keywords:list[str]=[]
    tag:list[str] =[]
    
    example_question:str
    example_answer:str = ""
    
    main_category:str 
    sub_category:str 

    files:list[str] = []
    status:Literal['solved','unsolved']="unsolved" #是否被解決 
    report:str #?
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("timestamp")
    def _serialize_timestamp(self, v: datetime):
        # Present as Asia/Taipei local time in ISO 8601 (e.g., 2025-09-10T12:34:56+08:00)
        return v.astimezone(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds")
    
class ContactPerson(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    
class MainCategoryConfig(BaseModel):
    description: list[str] = []
    sub: list[str] = []
    access: list[str] = []
    status: bool

class MainCategoriesCreate(BaseModel):
    # 僅這些 key 合法；沒出現在這裡的 key 會被直接擋掉
    # 內部以英文欄位名維護；對外用中文 key（alias）收/回資料。
    # 只允許下列欄位（extra='forbid'），未列出的 key 會被擋掉。
    company_description:str = ""
    
    quality_management: Optional[MainCategoryConfig] = Field(None, validation_alias="品質管理", serialization_alias="品質管理")    
    warehouse_management: Optional[MainCategoryConfig] = Field(None, validation_alias="倉儲管理", serialization_alias="倉儲管理"    )
    production_management: Optional[MainCategoryConfig] = Field(None, validation_alias="生產管理", serialization_alias="生產管理"    )
    customer_service: Optional[MainCategoryConfig] = Field(None, validation_alias="客戶服務", serialization_alias="客戶服務"    )
    procurement_management: Optional[MainCategoryConfig] = Field(None, validation_alias="採購管理", serialization_alias="採購管理"    )
    equipment_maintenance: Optional[MainCategoryConfig] = Field(None, validation_alias="設備維護", serialization_alias="設備維護"    )
    energy_management: Optional[MainCategoryConfig] = Field(None, validation_alias="能源管理", serialization_alias="能源管理"    )
    logistics_and_distribution: Optional[MainCategoryConfig] = Field(None, validation_alias="物流與配送", serialization_alias="物流與配送"    )
    r_n_d_innovation: Optional[MainCategoryConfig] = Field(None, validation_alias="研發與創新", serialization_alias="研發與創新"    )
    financial_management: Optional[MainCategoryConfig] = Field(None, validation_alias="財務管理", serialization_alias="財務管理"    )
    human_resources: Optional[MainCategoryConfig] = Field(None, validation_alias="人力資源", serialization_alias="人力資源"    )
    data_security_and_governance: Optional[MainCategoryConfig] = Field(None, validation_alias="數據安全與治理", serialization_alias="數據安全與治理"    )
    # extra='forbid'
    # 控制「額外 key」的處理方式。
    # Pydantic 預設是 extra='ignore'（沒定義的 key 會被丟掉），
    # 你這裡改成 forbid → 沒定義的 key 會直接報錯


class CompanyScheme(BaseModel):
    company_name: str
    company_type: list[str]
    company_unicode: str  # 統編
    company_property: list[str]
    contact_person: ContactPerson
    company_description: Optional[str] = ""   # 產業型態
    company_scale:str="",#50~100
    department_count:int
    language:str="zh"

class CompanyStructureListItem(BaseModel):
    department_name: str
    parent_department: str
    role: str  # 職責描述
    person_in_charge: ContactPerson

class CompanyStructureListItemDB(BaseModel):
    department_name: str
    parent_department: str
    role: str  # 職責描述
    person_in_charge_id: str



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
    
class CompanyStructureSetupScheme(BaseModel):
    departments:list[CompanyStructureListItem]
    
class DispenseDepartment(BaseModel):
    quality_management: Optional[list[str]] = Field(None, validation_alias="品質管理", serialization_alias="品質管理")    
    warehouse_management: Optional[list[str]] = Field(None, validation_alias="倉儲管理", serialization_alias="倉儲管理")
    production_management: Optional[list[str]] = Field(None, validation_alias="生產管理", serialization_alias="生產管理")
    customer_service: Optional[list[str]] = Field(None, validation_alias="客戶服務", serialization_alias="客戶服務")
    procurement_management: Optional[list[str]] = Field(None, validation_alias="採購管理", serialization_alias="採購管理")
    equipment_maintenance: Optional[list[str]] = Field(None, validation_alias="設備維護", serialization_alias="設備維護")
    energy_management: Optional[list[str]] = Field(None, validation_alias="能源管理", serialization_alias="能源管理")
    logistics_and_distribution: Optional[list[str]] = Field(None, validation_alias="物流與配送", serialization_alias="物流與配送")
    r_n_d_innovation: Optional[list[str]] = Field(None, validation_alias="研發與創新", serialization_alias="研發與創新")
    financial_management: Optional[list[str]] = Field(None, validation_alias="財務管理", serialization_alias="財務管理")
    human_resources: Optional[list[str]] = Field(None, validation_alias="人力資源", serialization_alias="人力資源")
    data_security_and_governance: Optional[list[str]] = Field(None, validation_alias="數據安全與治理", serialization_alias="數據安全與治理")


# 在原本HTTPException的基礎上加入data和code欄位
class CustomHTTPException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        # super()本身只會拿到父物件，如果需要call 父親物件的constructor需要手動另外呼叫
        super().__init__(status_code=status_code, detail=message)
        self.data = data
        
        
class  QuestionReponse(BaseModel):
    response:str

class ChatRecordCreate(BaseModel):
    ask: str
    answer: str
    user: str
    status:Literal['normal','suggest-solved','suggest-unsolved']
    reponse:QuestionReponse=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("timestamp")
    def _serialize_timestamp(self, v: datetime):
        # Present as Asia/Taipei local time in ISO 8601 (e.g., 2025-09-10T12:34:56+08:00)
        return v.astimezone(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds")
    
    
class ChatRecordEdit(BaseModel):
    ask: str =""
    answer: str =""
    user: str=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    reponse:QuestionReponse=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("timestamp")
    def _serialize_timestamp(self, v: datetime):
        # Present as Asia/Taipei local time in ISO 8601 (e.g., 2025-09-10T12:34:56+08:00)
        return v.astimezone(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds")
    