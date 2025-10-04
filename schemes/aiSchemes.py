from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class  QuestionReponse(BaseModel):
    response:str

class RecordCreate(BaseModel):
    ask: str
    answer: str
    user: str
    company:str=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    type:Literal['chat','auto-tagging','suggesting','embedding']
    reponse:QuestionReponse=""
    linked_knowledge_id:str="-1"
    elapse_time:str=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = ConfigDict(revalidate_instances='always')
    
class RecordEdit(BaseModel):
    ask: str =""
    answer: str =""
    user: str=""
    company:str=""
    type:Literal['chat','auto-tagging','suggesting']=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    reponse:QuestionReponse=""
    linked_knowledge_id:str=None
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(revalidate_instances='always')
    

class KnowledgeHistoryFilter(BaseFilter):
    _id:Optional[str]=None
    ask: str =None
    answer: str =None
    user: str=None
    type:Literal['chat','auto-tagging','suggesting']
    status:Literal['normal','suggest-solved','suggest-unsolved']=None
    reponse:QuestionReponse=None
    linked_knowledge_id:str=None

    
