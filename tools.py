from bson import ObjectId
from pydantic import BaseModel
from typing import TypeVar,Any, Dict, get_args, get_origin, Optional, List, Union
from datetime import datetime
import secrets

def token_generator(length:int=24):
    return secrets.token_urlsafe(length)

def bson_to_jsonable(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: bson_to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [bson_to_jsonable(v) for v in obj]
    return obj

M = TypeVar("M", bound=BaseModel)# 讓編譯器可以看得懂
def _ensure_model(data, model_type: type[M]) -> M:
    if isinstance(data, model_type):
        return data
    return model_type.model_validate(data)

def auto_build_mongo_filter(
    filter_model: type[BaseModel],
    filter_data: dict,
    time_field: str = "timestamp",
    fuzzy_fields: list[str] = None,) -> dict:
    mongo_filter = {}
    fuzzy_fields = fuzzy_fields or []

    for field_name, field in filter_model.model_fields.items():
        if field_name not in filter_data:
            continue  # 沒傳值就略過

        value = filter_data[field_name]
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        # 處理 List 型別欄位
        if origin == list:
            mongo_filter[field_name] = {"$in": value}

        # 處理 Optional[...] -> 取內部型別
        elif origin == Union and type(None) in args:
            # inner_type = args[0] if args[1] is type(None) else args[1]
            for i in args:
                if i is type(None):
                    continue
                elif i==list:
                    mongo_filter[field_name] = {"$in": value}
                elif i == str and field_name in fuzzy_fields:
                        mongo_filter[field_name] = {"$regex": value, "$options": "i"}
                else:
                    mongo_filter[field_name] = value

        if isinstance(value, datetime):
            continue
        # datetime 類的欄位要特別處理成範圍查詢
        
        if isinstance(value, str) and field_name in fuzzy_fields:
            mongo_filter[field_name] = {"$regex": value, "$options": "i"}
        else:
            mongo_filter[field_name] = value
    time_filter = {}
    if time_field:
        if "start_time" in filter_data:
            time_filter["$gte"] = filter_data["start_time"]
        if "end_time" in filter_data:
            time_filter["$lte"] = filter_data["end_time"]
        if time_filter:
            mongo_filter[time_field] = time_filter

    return mongo_filter