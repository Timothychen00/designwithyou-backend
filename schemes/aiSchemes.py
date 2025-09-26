from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

class  QuestionReponse(BaseModel):
    response:str

class RecordCreate(BaseModel):
    ask: str
    answer: str
    user: str
    company:str=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    type:Literal['chat','auto-tagging','suggesting']
    reponse:QuestionReponse=""
    elapse_time:str=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = ConfigDict(revalidate_instances='always')
    
class RecordEdit(BaseModel):
    ask: str =""
    answer: str =""
    user: str=""
    type:Literal['chat','auto-tagging','suggesting']=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    reponse:QuestionReponse=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(revalidate_instances='always')
    