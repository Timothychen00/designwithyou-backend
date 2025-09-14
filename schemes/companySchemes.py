from pydantic import BaseModel,EmailStr,Field
from typing import Literal,Optional

class ContactPerson(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    
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

