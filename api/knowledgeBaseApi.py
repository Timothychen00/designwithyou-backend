from fastapi import APIRouter,Request,Depends
from icecream import ic

from schemes import UserLoginScheme,ResponseModel,UserRegisterScheme,CustomHTTPException,MainCategoriesCreate,DispenseDepartment,KnowledgeSchemeCreate
from models import KnowledgeBase,Company,Chat,User
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


@router.post("/api/knowledge_base/knowledge")
async def create_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="admin"))):
    username = user_session.username
    user_profile = await User().get_user({"username":username}) # company_id
    # department
    # 
    data.department = user_profile['department']
    data.created_by = username
    
    # AI generate
    # main_category
    # sub_category
    
    result = await KnowledgeBase(request).create_knowledge(data)
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/chat')
async def chat():
    Chat().create_chat_record()
