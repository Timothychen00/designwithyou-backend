from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class KnowledgeSchemeCreate(BaseModel):
    _id:str
    company:str
    department:list[str]=[]
    keywords:list[str]=[]
    tag:list[str] =[]
    
    example_question:str
    embedding_example_question:list[float]=Field(default_factory=list)
    example_answer:str = ""
    
    main_category:str =""
    sub_category:str  =""

    files:list[str] = []
    status:Literal['solved','unsolved']="unsolved" #是否被解決 
    created_by:str="" #?
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MainCategoryConfig(BaseModel):
    description: list[str] = []
    sub: list[str] = []
    access: list[str] = []
    status: bool
    


class MainCategoriesCreate(BaseModel): #建立的時候Field是沒有預設值的，代表每一個欄位都是必填
    # company_description:str
    quality_management: Optional[MainCategoryConfig] = Field(..., validation_alias="品質管理", serialization_alias="品質管理")    
    warehouse_management: Optional[MainCategoryConfig] = Field(..., validation_alias="倉儲管理", serialization_alias="倉儲管理"    )
    production_management: Optional[MainCategoryConfig] = Field(..., validation_alias="生產管理", serialization_alias="生產管理"    )
    customer_service: Optional[MainCategoryConfig] = Field(..., validation_alias="客戶服務", serialization_alias="客戶服務"    )
    procurement_management: Optional[MainCategoryConfig] = Field(..., validation_alias="採購管理", serialization_alias="採購管理"    )
    equipment_maintenance: Optional[MainCategoryConfig] = Field(..., validation_alias="設備維護", serialization_alias="設備維護"    )
    energy_management: Optional[MainCategoryConfig] = Field(..., validation_alias="能源管理", serialization_alias="能源管理"    )
    logistics_and_distribution: Optional[MainCategoryConfig] = Field(..., validation_alias="物流與配送", serialization_alias="物流與配送"    )
    r_n_d_innovation: Optional[MainCategoryConfig] = Field(..., validation_alias="研發與創新", serialization_alias="研發與創新"    )
    financial_management: Optional[MainCategoryConfig] = Field(..., validation_alias="財務管理", serialization_alias="財務管理"    )
    human_resources: Optional[MainCategoryConfig] = Field(..., validation_alias="人力資源", serialization_alias="人力資源"    )
    data_security_and_governance: Optional[MainCategoryConfig] = Field(..., validation_alias="數據安全與治理", serialization_alias="數據安全與治理"    )
    # extra='forbid'
    # 控制「額外 key」的處理方式。
    # Pydantic 預設是 extra='ignore'（沒定義的 key 會被丟掉），
    # 你這裡改成 forbid → 沒定義的 key 會直接報錯
    
class KnowledgeBaseCreate(MainCategoriesCreate): #建立的時候Field是沒有預設值的，代表每一個欄位都是必填
    company_description:str
    
class MainCategoriesTemplate(BaseModel): # useing for reset the data
    company_description:str = ""
    quality_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="品質管理", serialization_alias="品質管理")    
    warehouse_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="倉儲管理", serialization_alias="倉儲管理"    )
    production_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="生產管理", serialization_alias="生產管理"    )
    customer_service: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="客戶服務", serialization_alias="客戶服務"    )
    procurement_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="採購管理", serialization_alias="採購管理"    )
    equipment_maintenance: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="設備維護", serialization_alias="設備維護"    )
    energy_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="能源管理", serialization_alias="能源管理"    )
    logistics_and_distribution: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="物流與配送", serialization_alias="物流與配送"    )
    r_n_d_innovation: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="研發與創新", serialization_alias="研發與創新"    )
    financial_management: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="財務管理", serialization_alias="財務管理"    )
    human_resources: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="人力資源", serialization_alias="人力資源"    )
    data_security_and_governance: Optional[MainCategoryConfig] = Field(MainCategoryConfig(status=False), validation_alias="數據安全與治理", serialization_alias="數據安全與治理"    )

class MainCategoriesUpdateScheme(BaseModel): # useing for reset the data
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

class SubCategoryAdd(BaseModel):
    main_category:str
    sub_category:str
    
class KnowledgeFilter(BaseFilter):
    main_category: Optional[list[str]] = None
    sub_category: Optional[list[str]] = None
    department: Optional[list[str]] = None
    created_by: Optional[list[str]] = None
    keywords: Optional[str] = None
    start_time: Optional[datetime] = Field(default=None, description="開始時間，用於 timestamp 篩選")
    end_time: Optional[datetime] = Field(default=None, description="結束時間，用於 timestamp 篩選")
    sort:Optional[str]=None
    content:Optional[str]=None
    limit:Optional[int]=None
    satrt_index:Optional[int]=None
    status:Optional[Literal['solved','unsolved']]=None