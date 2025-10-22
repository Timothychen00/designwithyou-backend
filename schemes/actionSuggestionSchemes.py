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
    recommand_priority:tuple[int,str]
    expect_outcome:str
    content:str
    company:str=""
    status:Literal['created','adopted','unadopted','inprogress','closed']="created"
    type:Literal['Operational',"Strategy",'Innovation']    
    assignee:str=""
    records:list[ActionContactRecord]=[]
    closed_timestamp:datetime =""
    inprogress_timestamp: datetime =""# 要完成的時間
    deadline_time_stamp:datetime=""
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ActionSuggestionEdit(BaseModel):
    title:Optional[str]=None
    recommand_priority:Optional[tuple[int,str]]=None
    expect_outcome:Optional[str]=None
    content:Optional[str]=None
    request_time: Optional[datetime] = None
    assignee:Optional[str]=None
    records:list[ActionContactRecord]=None
    closed_timestamp:datetime =None
    inprogress_timestamp: datetime=None
    status:Optional[Literal['created','adopted','unadopted','inprogress','closed']]=None
    deadline_time_stamp:datetime=None
    type:Optional[Literal['Operational',"Strategy",'Innovation']]=None

class ActionSuggestionFilter(BaseFilter):
    id: Optional[str] = Field(None, alias="_id")
    title:Optional[str]=None
    recommand_priority:Optional[tuple[int,str]]=None
    expect_outcome:Optional[str]=None
    content:Optional[str]=None
    company:str=None
    request_time: Optional[datetime] = None
    assignee:Optional[str]=None
    records:list[ActionContactRecord]=None
    closed_timestamp:datetime =None
    inprogress_timestamp: datetime=None
    status:Optional[Literal['created','adopted','unadopted','inprogress','closed']]=None
    deadline_time_stamp:datetime=None
    type:Optional[Literal['Operational',"Strategy",'Innovation']]=None
    
class ActionSuggestionAdopt(BaseModel):
    deadline_time_stamp:datetime
    

class ActionSuggestionReply(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username:str
    authority:str
    content:str