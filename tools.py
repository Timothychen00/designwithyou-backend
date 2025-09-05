from bson import ObjectId

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