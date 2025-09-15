from fastapi import APIRouter,Request,Depends,Query
from typing import Optional
from icecream import ic

from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models import KnowledgeBase,Company,AI,User,Statistic
from errors import BadInputError
from auth import login_required

router = APIRouter( tags=['KnowledgeBase'])

@router.get("/api/knowledge_base")
async def get_knowledge_base():
    pass
    return "1"

@router.post("/api/knowledge_base")
async def create_knowledge_base(request: Request ,main_category:MainCategoriesCreate,user_session=Depends(login_required(authority="admin"))):
    '''
    Step3
    '''
    company_id=user_session['company_id']
    ic(company_id)
    result={}
    result['category']=await KnowledgeBase(request).create_maincategory(main_category)
    result['company_description']=await Company(request).edit_company(company_id,{"company_description":main_category.company_description})
    return ResponseModel(message="ok", data=result)

@router.post("/api/knowledge_base/department_authority")
async def dispense_department(request:Request,data:DispenseDepartment):
    result = await KnowledgeBase(request).dispense_department(data)
    return ResponseModel(message="ok", data=result)

@router.get("/api/knowledge_base/knowledge")
async def get_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="normal"))):
    username = user_session['username']
    user_profile = await User(request).get_user({"username":username}) # company_id
    # department
    data.department = user_profile.get('department')
    result = await KnowledgeBase(request).create_knowledge(data)
    return ResponseModel(message="ok", data=result)

@router.post("/api/knowledge_base/knowledge")
async def create_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="admin"))):
    username = user_session['username']
    user_profile = await User(request).get_user({"username":username}) # company_id
    # department
    data.department = user_profile.get('department')
    if not data.department:
        raise BadInputError("User department is empty or disable")
    
    data.created_by = username
    
    # AI generate
    # main_category
    # sub_category
    
    result = await KnowledgeBase(request).create_knowledge(data)
    return ResponseModel(message="ok", data=result)

@router.get('/api/knowledge_base/knowledge_count',tags=['Statistics'])
async def get_knowledge_count(request:Request,user_session=Depends(login_required(authority="admin"))):
    svc = Statistic(request)
    company_id=user_session['company_id']
    filter={}
    result = await svc.get_knowledge_count(company_id,filter)
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/knowledge_count/filter',tags=['Statistics'])
async def get_knowledge_count_filtered(request:Request,filter:Optional[dict]=None,user_session=Depends(login_required(authority="admin"))):
    svc = Statistic(request)
    company_id=user_session['company_id']
    if not filter:
        filter={}
    result = await svc.get_knowledge_count(company_id,filter)
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/chat')
async def chat():
    AI().create_record()



# maincategory

@router.get('/api/knowledge_base/maincategory')
async def get_maincategory_list(request:Request):
    result = await KnowledgeBase(request).get_maincategory()
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/maincategory')
async def create_maincategory_list(request:Request,data:MainCategoriesCreate):
    result = await KnowledgeBase(request).create_maincategory(data)
    return ResponseModel(message="ok", data=result)

@router.put('/api/knowledge_base/maincategory')
async def edit_maincategory_list(request:Request,data:MainCategoriesUpdateScheme):
    result = await KnowledgeBase(request).edit_maincategory(data)
    return ResponseModel(message="ok", data=result)

@router.delete('/api/knowledge_base/maincategory')
async def reset_maincategory_list(request:Request):
    result = await KnowledgeBase(request).reset_maincategory()
    return ResponseModel(message="ok", data=result)


