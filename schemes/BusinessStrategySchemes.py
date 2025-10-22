from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class BusinessStrategySummaryItem(BaseModel):
    title:str
    content:str

class BusinessStrategyCreate(BaseModel):
    # _id:str
    department:list[str]=[]
    tags:list[str]=[]
    company:str=""
    main_category:str
    type:Literal['Operational',"Strategy",'Innovation']    
    summary:list[BusinessStrategySummaryItem]
    action_suggestion_id:list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BusinessStrategyEdit(BaseModel):
    # _id:str
    department:Optional[list[str]]=None
    tags:Optional[list[str]]=None
    company:Optional[str]=None
    main_category:Optional[str]=None
    type:Optional[Literal['Operational',"Strategy",'Innovation']]=None    
    summary:Optional[list[BusinessStrategySummaryItem]]=None
    action_suggestion_id:list[str]=None
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

class BusinessStrategyFilter(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    department:Optional[list[str]]=None
    tags:Optional[list[str]]=None
    company:Optional[str]=None
    main_category:Optional[str]=None
    type:Optional[Literal['Operational',"Strategy",'Innovation']]
    action_suggestion_id:list[str]=None
    summary:Optional[list[BusinessStrategySummaryItem]]=None
    
    limit: Optional[int] = None
    start_index: Optional[int] = None
    start_time: Optional[datetime]
    end_time: Optional[datetime]
