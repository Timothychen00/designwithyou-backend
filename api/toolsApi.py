from fastapi import APIRouter,Request,Depends,Query
from typing import Literal

from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.userModel import User
from auth import login_required
from models.statisticsModel import Statistic
from schemes.userSchemes import UserFilter,LoginHistoryFilter,LoginHistoryFilterTimeGroup
from tools import trace
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/api/tools",tags=['Tools'])

@trace
@router.delete("/clear_history",response_model=ResponseModel)
async def clear_history(request:Request):
    import trace_report
    await trace_report.clear()
    return ResponseModel(message='ok')

@trace
@router.get("/analysis",response_model=ResponseModel)
async def analysis(request:Request):
    import trace_report
    result = await run_in_threadpool(trace_report.main, [])
    return ResponseModel(message="ok", data=result)
