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
import json
import os
import threading
from errors import BadInputError

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
def _ensure_model(data:dict| type[M], model_type: type[M]) -> M:
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
        if field_name=='id':
            continue
        if field_name not in filter_data:
            continue  # 沒傳值就略過
        
        if field_name=='start_time' or field_name=='end_time':
            continue

        value = filter_data[field_name]
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        # 處理 List 型別欄位
        if isinstance(value, list):
            mongo_filter[field_name] = {"$in": value}
            continue

        # 處理 Optional[...] -> 取內部型別
        elif origin == Union and type(None) in args:
            # inner_type = args[0] if args[1] is type(None) else args[1]
            for i in args:
                if i is type(None):
                    continue
                elif get_origin(i) == list:
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

    if 'id' in filter_data:
        try:
            if isinstance(filter_data['id'],list):
                ids=[]
                for i in filter_data['id']:
                    ids.append(ObjectId(i))
                mongo_filter["_id"]={"$in":ids}
            else:
                mongo_filter["_id"]=ObjectId(filter_data['id'])
            

                value=ObjectId(filter_data['id'])
                mongo_filter['_id']=value
        except:
            raise BadInputError("id not in format")
            
    return mongo_filter


def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

_trace_state: ContextVar[dict[str, List[dict]]] = ContextVar("_trace_state", default=None)

# local trace files (placed next to this module)
_TRACE_LOG_PATH = os.path.join(os.path.dirname(__file__), "trace_calls.json")
_TRACE_AGG_PATH = os.path.join(os.path.dirname(__file__), "trace_aggregates.json")
_TRACE_SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "trace_summary.json")
_trace_lock = threading.Lock()

def _write_trace_records(records: list[dict]):
    """Append raw call records to a JSON log and update aggregate summary files.

    Writes three files next to this module:
    - trace_calls.json : one JSON object per line for each recorded function call
    - trace_aggregates.json : mapping of function -> stats (count, total, avg, max, last_seen)
    - trace_summary.json : list of aggregated stats sorted by total desc (for quick inspection)
    """
    with _trace_lock:
        try:
            # append per-call entries
            with open(_TRACE_LOG_PATH, 'a', encoding='utf-8') as f:
                for r in records:
                    entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "name": r.get("name"),
                        "level": r.get("level"),
                        "duration": r.get("duration"),
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # load existing aggregates
            aggregates = {}
            if os.path.exists(_TRACE_AGG_PATH):
                try:
                    with open(_TRACE_AGG_PATH, 'r', encoding='utf-8') as fa:
                        aggregates = json.load(fa)
                except Exception:
                    # if file corrupted or unreadable, start fresh
                    logging.exception("Could not read existing trace aggregates, starting fresh")
                    aggregates = {}

            # update aggregates with these records
            for r in records:
                name = r.get("name")
                d = float(r.get("duration", 0.0))
                stats = aggregates.get(name, {"count": 0, "total": 0.0, "max": 0.0, "last_seen": None})
                stats["count"] = int(stats.get("count", 0)) + 1
                stats["total"] = float(stats.get("total", 0.0)) + d
                stats["avg"] = stats["total"] / stats["count"]
                stats["max"] = max(float(stats.get("max", 0.0)), d)
                stats["last_seen"] = datetime.utcnow().isoformat() + "Z"
                aggregates[name] = stats

            # persist aggregates
            with open(_TRACE_AGG_PATH, 'w', encoding='utf-8') as fa:
                json.dump(aggregates, fa, ensure_ascii=False, indent=2)

            # write sorted summary (by total duration desc)
            summary = [ {"name": name, **v} for name, v in aggregates.items() ]
            summary.sort(key=lambda x: x.get("total", 0.0), reverse=True)
            with open(_TRACE_SUMMARY_PATH, 'w', encoding='utf-8') as fs:
                json.dump(summary, fs, ensure_ascii=False, indent=2)

        except Exception as e:
            logging.exception("Failed to write trace records: %s", e)

def _before_call(func):
    state = _trace_state.get()
    is_root = False
    if state is None:
        state = {"stack": [], "records": []}
        _trace_state.set(state)
        is_root = True

    level = len(state["stack"])
    record = {
        "name": func.__qualname__,
        "level": level,
        "start": time.perf_counter(),
    }
    state["stack"].append(record)
    state["records"].append(record)
    return state, record, is_root

def _after_call(state, record, is_root):
    record["end"] = time.perf_counter()
    record["duration"] = record["end"] - record["start"]
    state["stack"].pop()

    if is_root:
        # write logs and update aggregates
        try:
            _write_trace_records(state["records"])
        finally:
            # keep console output for quick dev feedback
            try:
                print("\n╭─── Trace Summary ───")
                for r in state["records"]:
                    indent = "│  " * r["level"]
                    print(f"{indent}├─ {r['name']} took {r['duration']:.4f}s")
                print("╰─────────────────────\n")
            except Exception:
                pass
            _trace_state.set(None)

def trace(func):
    is_coroutine = asyncio.iscoroutinefunction(func)

    if is_coroutine:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            state, record, is_root = _before_call(func)
            try:
                return await func(*args, **kwargs)
            finally:
                _after_call(state, record, is_root)
        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        state, record, is_root = _before_call(func)
        try:
            return func(*args, **kwargs)
        finally:
            _after_call(state, record, is_root)
    return sync_wrapper
