from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .utilitySchemes import BaseFilter

class  QuestionReponse(BaseModel):
    response:str

class RecordCreate(BaseModel):
    ask: str
    prompt:str=None
    answer: str
    user: str
    company:str=""
    department:Optional[list[str]]=None
    main_category:Optional[str]=None
    sub_category:Optional[str]=None
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    type:Literal['chat','auto-tagging','suggesting','embedding','rewrite']
    reponse:QuestionReponse=""
    linked_knowledge_id:str="-1"
    elapse_time:str=""
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = ConfigDict(revalidate_instances='always')
    
class RecordEdit(BaseModel):
    ask: str =""
    prompt:str=None
    answer: str =""
    user: str=""
    company:str=""
    department:Optional[list[str]]=None
    main_category:Optional[str]=None
    sub_category:Optional[str]=None
    type:Literal['chat','auto-tagging','suggesting','embedding','rewrite']=""
    status:Literal['normal','suggest-solved','suggest-unsolved']="normal"
    reponse:QuestionReponse=""
    linked_knowledge_id:str=None
    # Store as timezone-aware UTC datetime; auto-fill on creation
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(revalidate_instances='always')
    

class KnowledgeHistoryFilter(BaseFilter):
    id: Optional[str] = Field(None, alias="_id")
    ask: str =None
    prompt:str=None
    answer: str =None
    user: str=None
    department:Optional[list[str]]=None
    main_category:Optional[list[str]]=None
    sub_category:Optional[list[str]]=None
    type:Literal['chat','auto-tagging','suggesting','embedding','rewrite']="chat"
    status:Literal['normal','suggest-solved','suggest-unsolved']=None
    reponse:QuestionReponse=None
    linked_knowledge_id:str=None
    
class KnowledgeHistoryGroup(BaseModel):
    main_category:bool=False
    sub_category:bool=False

# class MaincategoryHistoryFilter(BaseFilter):
#     id: Optional[str] = Field(None, alias="_id")
#     ask: str =None
#     answer: str =None
#     user: str=None
#     department:Optional[list[str]]=None
#     main_category:Optional[str]
#     sub_category:Optional[str]=None
#     type:Literal['chat','auto-tagging','suggesting']="chat"
#     status:Literal['normal','suggest-solved','suggest-unsolved']=None
#     reponse:QuestionReponse=None
#     linked_knowledge_id:str=None