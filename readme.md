# Mongodb
因為mongodb預設的連線方式是同步的，但是fastapi是非同步的所以需要使用motor作為driver進行使用


# DesignWithYou Backend

這是 DesignWithYou 專案的後端程式碼，使用 FastAPI 搭建，並整合 session-based authentication、權限分級、MongoDB 操作等功能。

---

## 使用技術

- **FastAPI**：Python 的現代、非同步 Web 框架
- **Starlette**：FastAPI 所依賴的 ASGI 工具庫，提供 Middleware 支援
- **Uvicorn**：ASGI Server，用來啟動應用程式
- **Motor**：非同步 MongoDB driver，取代 pymongo
- **Pydantic**：資料驗證與序列化
- **SessionMiddleware**：以 Cookie-based session 管理登入狀態

---

## 如何啟動專案

### 1.安裝依賴套件
```bash
pip install pipenv
pipenv install
```

### 2. 設定ENV文件
在目錄建立.env
DB_USER=雲端DB使用者
DB_PASSWORD=雲端DB密碼
MODE=DB模式（remote/local）
*如果使用local模式可以使用之前開發的local mongo的組件用DB命令啟動本地的開發DB*

### 3.啟動伺服器（開發模式）
```bash
pipenv run uvicorn app:app --reload
```

伺服器將啟動於 `http://127.0.0.1:8000`

---

## 查看 API 文件

FastAPI 內建提供 Swagger 文件：
- **Swagger UI**：`http://localhost:8000/docs`
- **ReDoc**：`http://localhost:8000/redoc`

---

## 登入與權限機制

### 登入方式：
```http
POST /login
Content-Type: application/json

{
  "account": "your_account",
  "password": "your_password"
}
```

登入成功後，後端會將使用者資訊儲存在 session（cookie）中。

---

### 權限分級（位於 `auth.py`）

登入後 `request.session["login"]` 會儲存如下資訊：

```json
{
  "id": "user123",
  "authority": "normal" | "admin" | "owner"
}
```

對應權限說明如下：

| 權限等級 | 說明 |
|----------|------|
| `normal` | 一般使用者，權限最少，通常是一般員工使用者 |
| `admin`  | 管理者，可管理一般使用者，通常是HR |
| `owner`  | 擁有者，具有最高權限，通常是企業擁有者 |
*註冊後權限預設是normal，需要去db裡面進行設定*

權限檢查透過 `Depends(login_required(...))` 自動套用於路由上，例如：

```python
@app.get("/admin-panel")
async def admin_view(user=Depends(login_required("admin"))):
    ...
```

---

## 測試方式

可使用以下工具進行測試：

### 方法一：使用 Swagger `/docs`
- 登入 `/login`
- 再訪問需登入或權限驗證的路由（如 `/checkauth`）

注意：Swagger UI 會自動儲存 cookie

---

### 方法二：使用 curl 測試 session 保留
參考test資料夾

```bash
# 登入並保存 session cookie
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}' \
  -c cookies.txt

# 帶入 cookie 呼叫保護 API
curl -X GET http://localhost:8000/checkauth \
  -b cookies.txt
```

## 專案架構簡介

```bash
.
├── app.py           # FastAPI app 與路由定義
├── models.py        # 使用者與資料操作邏輯
├── auth.py          # 權限驗證與 login_required 實作
├── schemes.py       # 回應格式與錯誤類型定義
├── Pipfile          # 套件管理
└── readme.md        # 說明文件
```


## 測試資料
- /api/company/setup_company_structure
  - 
    ```json
  {
  "departments": [
    {
      "department_name": "總部",
      "parent_department": "無",
      "role": "-",
      "person_in_charge": {
        "name": "蔡寒寒",
        "email": "cai.hanhan@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "營運部",
      "parent_department": "總部",
      "role": "負責門市營運與績效管理",
      "person_in_charge": {
        "name": "王小明",
        "email": "wang.xiaoming@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "客戶服務中心",
      "parent_department": "總部",
      "role": "統一處理消費者客服與回饋",
      "person_in_charge": {
        "name": "陳敏萱",
        "email": "chen.minxuan@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "商品部",
      "parent_department": "營運部",
      "role": "商品企劃、品牌與供應商管理",
      "person_in_charge": {
        "name": "郭琳林",
        "email": "guo.linlin@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "採購部",
      "parent_department": "營運部",
      "role": "負責與品牌商洽談與採購管理",
      "person_in_charge": {
        "name": "文品文",
        "email": "wen.pinwen@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "人力資源部",
      "parent_department": "總部",
      "role": "人才招募、教育訓練與組織發展",
      "person_in_charge": {
        "name": "陳大大",
        "email": "chen.dada@example.com",
        "phone": ""
      }
    },
    {
      "department_name": "行銷企劃部",
      "parent_department": "總部",
      "role": "廣告促銷、社群經營與活動企劃",
      "person_in_charge": {
         "name": "林木森",
        "email": "lin.musen@example.com"

      }
    }
  ]
}
        ```