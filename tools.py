from bson import ObjectId
from pydantic import BaseModel
from typing import TypeVar
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

