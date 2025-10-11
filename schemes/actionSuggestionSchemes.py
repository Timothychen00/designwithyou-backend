from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class ActionContactRecord(BaseModel):
    role:str
    content:str
    name:str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ActionSuggestionCreate(BaseModel):
    # _id:str
    title:str
    recommand_priority:list[int,str]
    expect_outcome:str
    department:list[str]
    content:str
    status:Literal['']
    type:Literal['Operational',"Strategy",'Innovation']    
    request_time: datetime
    assignee:str
    records:ActionContactRecord
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ActionSuggestionFilter(BaseFilter):
    _id:Optional[str]=None
    title:Optional[str]=None
    recommand_priority:Optional[list[int,str]]=None
    expect_outcome:Optional[str]=None
    department:Optional[list[str]]=None
    content:Optional[str]=None
    request_time: Optional[datetime] = None
    assignee:Optional[str]=None
    records:ActionContactRecord=None
    status:Optional[Literal['created','inprogress','done']]=None
    type:Optional[Literal['Operational',"Strategy",'Innovation']]=None
