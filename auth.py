from fastapi import Request

from schemes import CustomHTTPException

def login_required(authority: str):
    async def checker(request: Request):
        if "login" not in request.session:
            raise CustomHTTPException(status_code=401, message="Not Logged In")
        session_auth = request.session["login"].get("authority")
        if authority == "owner" and session_auth != "owner":
            raise CustomHTTPException(status_code=403, message="Not Permitted!")
        if authority == "admin" and session_auth == "normal":
            raise CustomHTTPException(status_code=403, message="Not Permitted!")
        return request.session["login"]
    return checker