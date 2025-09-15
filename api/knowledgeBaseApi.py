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
    建立新的主分類 (Main Category)，同時更新公司簡介 (company_description)

    權限：必須為 admin

    參數:
        request (Request): FastAPI 的請求物件，內含 session、company 資訊等
        main_category (MainCategoriesCreate): 主分類建立用的資料 scheme，應包含分類名稱、描述、是否啟用等欄位，以及公司簡介字段 (company_description)
        user_session: 由 login_required 授權中間件提供，包含 user 的身份與公司 ID

    處理流程：
        1. 從 session 拿到 company_id
        2. 呼叫 KnowledgeBase.create_maincategory() 建立主分類紀錄
        3. 呼叫 Company.edit_company 更新公司描述 (company_description)
        4. 封裝 response

    回傳:
        ResponseModel: 
            message: 操作狀態 ("ok" 或錯誤訊息)
            data: 包含 `category`（新建主分類的資料）與 `company_description`（更新後的公司簡介）

    錯誤情況:
        - 權限不足會被 login_required 攔截
        - main_category 資料不符合 schema 驗證會丟出 validation error
        - 資料庫操作失敗可能拋出其他例外
    '''
    company_id=user_session['company_id']
    ic(company_id)
    result={}
    result['category']=await KnowledgeBase(request).create_maincategory(main_category)
    result['company_description']=await Company(request).edit_company(company_id,{"company_description":main_category.company_description})
    return ResponseModel(message="ok", data=result)

@router.post("/api/knowledge_base/department_authority")
async def dispense_department(request:Request,data:DispenseDepartment):
    """
    分配／設定哪個部門對主分類／知識庫項目具有使用或管理權限

    權限：預設需要管理員或有相應權限才能執行（視 dispense_department 內部實作而定）

    參數：
        request (Request): 請求物件
        data (DispenseDepartment): 包含要分配權限的部門、分類或條目等資訊 schema

    回傳：
        ResponseModel:
            message: 操作結果
            data: 分配後的結果（可能是更新後的部門權限映射）

    錯誤情況：
        - 權限不足
        - 傳入 data 欄位不正確
        - 所指定的部門或分類不存在等錯誤
    """
    result = await KnowledgeBase(request).dispense_department(data)
    return ResponseModel(message="ok", data=result)

@router.get("/api/knowledge_base/knowledge")
async def get_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="normal"))):
    """
    讀取／搜尋知識條目 (Knowledge Items)

    權限：最低為 normal

    參數：
        request (Request): 請求物件，用以取得例如 company 或 user 資訊
        data (KnowledgeSchemeCreate): 查詢條件，例如主分類、副分類、關鍵字等
        user_session: 登入後的使用者資訊，至少為 normal 權限

    處理流程：
        1. 依 username 拿到 user profile（含 company_id, department 等）
        2. 把使用者的 department 放入 data.department，以確保查詢依部門權限過濾
        3. 呼叫 KnowledgeBase.create_knowledge(data)（這裡名稱 “create_knowledge” 可能是查詢或建立的混用，要確認內部實作）
        4. 返回查詢結果

    回傳：
        ResponseModel:
            message: 操作訊息 ("ok" 或錯誤)
            data: 查詢到的知識條目清單或頁面資訊

    錯誤情況：
        - 權限不足
        - 使用者未設定部門（department 為空）會可能造成查詢時無法分配篩選
        - 傳入 data 欄位格式錯誤
    """
    username = user_session['username']
    user_profile = await User(request).get_user({"username":username}) # company_id
    # department
    data.department = user_profile.get('department')
    result = await KnowledgeBase(request).create_knowledge(data)
    return ResponseModel(message="ok", data=result)

@router.post("/api/knowledge_base/knowledge")
async def create_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="admin"))):
    """
    建立新的知識條目 (Knowledge Item)

    權限：必須為 admin

    參數：
        request (Request): 請求物件
        data (KnowledgeSchemeCreate): 包含知識內容、主／副分類、狀態、部門等欄位
        user_session: 登入後的使用者資訊

    處理流程：
        1. 取得 username 與 user profile（有 department）
        2. 若 department 欄位為空或被停用，拋出 BadInputError
        3. 設定 created_by 為 username
        4. 呼叫 KnowledgeBase.create_knowledge(data) 來建立記錄

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 新建立的知識條目資料

    錯誤情況：
        - 權限不足
        - department 欄位缺失或停用
        - schema 驗證失敗
        - 資料庫操作錯誤
    """
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
    """
    取得公司整體知識條目的總數量

    權限：admin

    參數：
        request (Request): 請求物件
        user_session: 包含公司 ID 與權限

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 一個物件，至少包含各分類或總計的知識條目數量

    錯誤情況：
        - 權限不足
        - 資料庫查詢錯誤
    """
    svc = Statistic(request)
    company_id=user_session['company_id']
    filter={}
    result = await svc.get_knowledge_count(company_id,filter)
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/knowledge_count/filter',tags=['Statistics'])
async def get_knowledge_count_filtered(request:Request,filter:Optional[dict]=None,user_session=Depends(login_required(authority="admin"))):
    """
    取得知識條目的數量，但可依指定條件過濾

    權限：admin

    參數：
        request (Request): 請求物件
        filter (Optional[dict]): 可選的過濾條件，例如特定主分類、副分類、部門、狀態等
        user_session: 使用者 session，含 company_id 與權限

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 過濾後的知識條目數量統計

    錯誤情況：
        - 權限不足
        - filter 格式不正確
        - 查詢失敗
    """
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
    """
    取得主分類 (Main Categories) 的清單

    權限：可公開或有登入要求（看實作是否需要 session），目前這 route 沒加 login_required，所以可能是公開或只需 login

    參數：
        request (Request): 請求物件

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 主分類的清單（包含名稱、描述、啟用狀態等）
    """
    result = await KnowledgeBase(request).get_maincategory()
    return ResponseModel(message="ok", data=result)

@router.post('/api/knowledge_base/maincategory')
async def create_maincategory_list(request:Request,data:MainCategoriesCreate):
    """
    建立新的主分類（Main Category）

    權限：未指定 login_required，目前這 route 沒有 Depends(login_required)，要確認是否需要授權

    參數：
        request (Request)
        data (MainCategoriesCreate): 主分類的建立資料

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 建立後的主分類內容
    """
    result = await KnowledgeBase(request).create_maincategory(data)
    return ResponseModel(message="ok", data=result)

@router.put('/api/knowledge_base/maincategory')
async def edit_maincategory_list(request:Request,data:MainCategoriesUpdateScheme):
    """
    修改／編輯現有主分類內容

    權限：未指定，目前沒有 login_required，需要確認是否要限制

    參數：
        request (Request)
        data (MainCategoriesUpdateScheme): 主分類更新資料，如名稱、描述、狀態等

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 更新後的主分類內容
    """
    result = await KnowledgeBase(request).edit_maincategory(data)
    return ResponseModel(message="ok", data=result)

@router.delete('/api/knowledge_base/maincategory')
async def reset_maincategory_list(request:Request):
    """
    重置／刪除所有主分類列表

    注意：此操作可能會清空所有主分類資料

    權限：未指定 login_required，目前無權限控制，應額外加限制以防誤刪

    參數：
        request (Request)

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 重置後的狀態或空清單
    """
    result = await KnowledgeBase(request).reset_maincategory()
    return ResponseModel(message="ok", data=result)


