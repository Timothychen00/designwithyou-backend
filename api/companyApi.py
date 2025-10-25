from fastapi import APIRouter,Request,Depends,Query, Body

from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.companyModel import Company
from models.statisticsModel import Statistic
from models.userModel import User
from tools import trace
from auth import login_required

router = APIRouter( tags=['Company'])

@trace
@router.get("/api/company")
async def get_company(request: Request,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    company_id=user_session["company"]
    company = await svc.get_company(company_id)
    return ResponseModel(message="ok", data=company)

@trace
@router.post("/api/company")
async def create_company(request: Request, payload: CompanyScheme = None,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    if not payload:
        username=user_session['username']
        company_id = await svc.create_empty_company(username)
        return ResponseModel(message="empty company created", data={"company": company_id})
    else:
        company_id = await svc.create_company(payload)
        return ResponseModel(message="company created", data={"company": company_id})
    
@trace
@router.put("/api/company")
async def edit_company(request: Request, company_id: str, data: CompanyScheme,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.edit_company(company_id, data)
    return ResponseModel(message="updated", data={"status": result})

@trace
@router.delete("/api/company")#記得要改使用者那邊
async def delete_company(request: Request, company_id: str ,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.delete_company(company_id)
    return ResponseModel(message="deleted", data={"status": result})

@trace
@router.post("/api/company/setup_company_structure")
async def setup_company_structure(request: Request,company_id: str ,departments:CompanyStructureSetupScheme ):
    svc = Company(request)
    result = await svc.setup_company_structure(company_id,departments)
    return ResponseModel(message="ok", data=result)

@trace
@router.get("/api/company/department")#記得要改使用者那邊
async def get_departments(request: Request, company_id: str ,user_session=Depends(login_required(authority="admin"))):
    svc = Company(request)
    result = await svc.get_company_departmentlist(company_id)
    return ResponseModel(message="ok", data=result)

@trace
@router.get('/api/company/employee')
async def get_employee(request: Request, company_id: str ,user_session=Depends(login_required(authority="admin"))):
    svc = User(request)
    result = await svc.get_users({},company_id=company_id)
    
    mask = [
        "username", "authority", "name", "company", "phone", "role", "note", "department"
    ]
    if result:
        filtered_records = [
            {field: record.get(field) for field in mask if field in record}
            for record in result if record is not None
        ]
        result = filtered_records if isinstance(result, list) or hasattr(result, "to_list") else (filtered_records[0] if filtered_records else None)
    return ResponseModel(message="ok", data=result)

@trace
@router.get('/api/company/employee_count',tags=['Statistics'])
async def get_employee_count(request: Request ,user_session=Depends(login_required(authority="admin"))):
    svc = Statistic(request)
    company_id=user_session["company"]
    result = await svc.get_company_employee_count(company_id)
    return ResponseModel(message="ok", data=result)