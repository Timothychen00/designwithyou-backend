from bson import ObjectId
from pydantic import BaseModel
from typing import TypeVar,Any, Dict, get_args, get_origin, Optional, List, Union
from datetime import datetime
import secrets
import time
from contextvars import ContextVar
import asyncio
import time
import inspect
import functools
import inspect
import logging
from contextvars import ContextVar
import numpy as np

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
        
        if field_name=='start_time' or field_name=='end_time':
            continue

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


def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

_trace_stack: ContextVar[List[dict]] = ContextVar("_trace_stack", default=[])

def trace(func):
    is_coroutine = asyncio.iscoroutinefunction(func)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        stack = _trace_stack.get()
        level = len(stack)
        record = {
            "name": func.__qualname__,
            "level": level,
            "start": time.perf_counter()
        }
        stack.append(record)
        _trace_stack.set(stack)

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            record["end"] = time.perf_counter()
            record["duration"] = record["end"] - record["start"]
            if level == 0:
                print("\n╭─── Trace Summary ───")
                for r in stack:
                    indent = "│  " * r["level"]
                    print(f"{indent}├─ {r['name']} took {r['duration']:.4f}s")
                print("╰─────────────────────\n")
                _trace_stack.set([])
            else:
                stack[level] = record

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        stack = _trace_stack.get()
        level = len(stack)
        record = {
            "name": func.__qualname__,
            "level": level,
            "start": time.perf_counter()
        }
        stack.append(record)
        _trace_stack.set(stack)

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            record["end"] = time.perf_counter()
            record["duration"] = record["end"] - record["start"]
            if level == 0:
                print("\n╭─── Trace Summary ───")
                for r in stack:
                    indent = "│  " * r["level"]
                    print(f"{indent}├─ {r['name']} took {r['duration']:.4f}s")
                print("╰─────────────────────\n")
                _trace_stack.set([])
            else:
                stack[level] = record

    return async_wrapper if is_coroutine else sync_wrapper