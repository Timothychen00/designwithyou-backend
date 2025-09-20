from fastapi import APIRouter,Request,Depends,Query
from typing import Optional
from icecream import ic

from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,SubCategoryAdd,KnowledgeFilter
from schemes.utilitySchemes import CustomHTTPException,ResponseModel
from models.knowledgeModel import KnowledgeBase
from models.companyModel import Company
from models.userModel import User
from models.statisticsModel import Statistic
from models.aiModel import AI
from models.settingsModel import Settings
from errors import BadInputError,StatusError,AIError
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
    company_id=user_session["company"]
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
async def get_knowledge(request:Request,data_filter:KnowledgeFilter=Depends(KnowledgeFilter),user_session=Depends(login_required(authority="normal"))):
    """
    查詢知識庫條目（Knowledge Items），可依多種條件篩選，並根據使用者部門權限限制結果範圍。

    權限：需登入且具備 normal 權限等級。

    參數：
        request (Request): FastAPI 請求物件
        data_filter (KnowledgeFilter): 查詢條件過濾器，支援以下欄位：
            - main_category: 多個主分類名稱
            - sub_category: 多個子分類名稱
            - department: 多個部門（此欄位由系統根據登入者自動設定）
            - created_by: 建立者使用者名稱
            - keyword: 搜索keywords欄位
            - content:模糊搜索【問題】
            - start_time, end_time: 篩選 timestamp 時間範圍
            - limit: 回傳最大筆數（若未指定，則預設查全部）
            - start_index: 起始筆數（用於分頁）
        user_session (dict): 授權中介層注入的登入者資訊（含 username、company_id）

    查詢邏輯：
        1. 從 session 中取得登入者 username
        2. 讀取該使用者 profile，取得其所屬部門列表
        3. 自動將部門設定進 `data_filter.department`
        4. 將 filter 傳入 KnowledgeBase.get_knowledge()，並執行 MongoDB 查詢

    回傳：
        ResponseModel:
            message: 操作狀態（"ok" 或錯誤訊息）
            data: 符合條件的知識條目清單（List[dict]）

    錯誤情況：
        - 權限不足會被 login_required 攔截
        - 使用者不存在或無部門設定時，仍會執行查詢但部門條件為空
        - 查詢資料庫失敗會由底層拋出例外
    """
    username = user_session['username']
    user_profile = await User(request).get_user({"username":username}) # company_id
    # department
    data_filter.department = user_profile.get('department',[])
    result = await KnowledgeBase(request).get_knowledge(data_filter)
    return ResponseModel(message="ok", data=result)

@router.post("/api/knowledge_base/load_preset_knowledge")
async def load_preset_knowledge(request:Request,user_session=Depends(login_required(authority="admin"))):
    companyid = user_session['company']
    user_profile=await User(request).get_user({"username":user_session['username']})
    company_profile = await Company(request).get_company(companyid)
    
    category_dict={}
    settings = await Settings(request).get_settings()
    for i in settings['category']:
        if settings['category'][i]['status']:
            category_dict[i]=settings['category'][i]['sub']
            
    ic(category_dict)
    result=await AI(request).generate_knowlege(company_profile,category_dict,user_profile,20)
    return ResponseModel(message="ok", data=result)


@router.post("/api/knowledge_base/knowledge/request")
async def request_knowledge(request:Request,data:KnowledgeSchemeCreate,user_session=Depends(login_required(authority="admin"))):
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
    success=False
    ai_result=""
    for retry in range(3):
        main_category=await KnowledgeBase(request).get_maincategory()
        if not main_category:
            raise StatusError("please setup main_category first")
        ai_result=await AI(request).auto_tagging(main_category,data.example_question,user_profile)
        
        if ai_result in main_category:
            success=True
            break
        
    if success==False:
        raise AIError(f"AI response not expected with retried {retry} times!")

    data.main_category=ai_result

    success=False
    ai_result=""
    for retry in range(3):
        try:
            sub_category=await KnowledgeBase(request).get_subcategory(data.main_category)

            ai_result=await AI(request).auto_tagging(sub_category,data.example_question,user_profile,extend=True)
            
            if ai_result not in sub_category:
                await KnowledgeBase(request).add_subcategory(data.main_category,ai_result)
            success=True
        except:
            success=False
            ic(f"sub category retry {retry}")
        # if ai_result in main_category:
        #     success=True
        #     break
        
    if success==False:
        raise AIError(f"AI response not expected with retried {retry} times!")
    
    data.sub_category=ai_result
    
    result = await KnowledgeBase(request).create_knowledge(data)
    return ResponseModel(message="ok", data=result)

@router.get('/api/knowledge_base/ask')
async def ask(request:Request,data:str,user_session=Depends(login_required(authority="normal"))):
    profile=await User(request).get_user({"username":user_session['username']})
    if not profile:
        raise BadInputError("User not exist!")
    
    if profile['department']==[]:
        raise BadInputError("User department unset!")
    departments=profile['department']
    
    settings=await Settings(request).get_settings()
    main_categories=settings['category']
    
    
    filtered_main_categories=[]
    for each_main_category in main_categories:
        ic(each_main_category)
        temp_intersection= list(set(each_main_category['access']) & set(departments))
        ic(temp_intersection)
        
        if temp_intersection : # not empty  ->permitted
            ic(each_main_category)
            filtered_main_categories.append(each_main_category)
    ic(filtered_main_categories)
    
    result = await AI(request).ask_ai()
    return result 
    


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
    company_id=user_session['company']
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
    company_id=user_session["company"]
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
    取得主構面 (Main Categories) 的清單

    參數：
        request (Request): 請求物件

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 主構面的清單
    """
    result = await KnowledgeBase(request).get_maincategory()
    return ResponseModel(message="ok", data=result)

@router.get('/api/knowledge_base/subcategory')
async def get_subcategory_list(request:Request,main_category:str):
    """
    取得子構面 (Sub Categories) 的清單

    參數：
        request (Request): 請求物件
        main_category:主構面名稱

    回傳：
        ResponseModel:
            message: 操作訊息
            data: 子構面的清單
    """
    result = await KnowledgeBase(request).get_subcategory(main_category)
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


@router.post('/api/knowledge_base/subcategory')
async def add_subcategory(request:Request,data:SubCategoryAdd):
    """
    參數：
        request (Request)
        str (str): 子構面的建立資料

    回傳：
        ResponseModel:
            message: 操作訊息
    """
    result = await KnowledgeBase(request).add_subcategory(data.main_category,data.sub_category)
    return ResponseModel(message="ok", data=result)