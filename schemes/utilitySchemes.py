from pydantic import BaseModel,EmailStr,Field,field_serializer,ConfigDict, ValidationError
from typing import Literal,Optional,Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException

from tools import bson_to_jsonable

class ResponseModel(BaseModel):
    success: bool = True
    status_code: int = 200 
    message: str # 提示訊息
    data: Optional[Any] = None #如果需要夾帶資料的話可以放這裡

    @field_serializer('data') # 針對data這個欄位進行客製化的serialize，解決bson會出現的問題
    def serialize_data(self, v):
        return bson_to_jsonable(v)  # 低迴進行控制
    
ResponseModel.model_rebuild()

# 在原本HTTPException的基礎上加入data和code欄位
class CustomHTTPException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        # super()本身只會拿到父物件，如果需要call 父親物件的constructor需要手動另外呼叫
        super().__init__(status_code=status_code, detail=message)
        self.data = data
