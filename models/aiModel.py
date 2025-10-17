from fastapi import FastAPI, HTTPException, Request
from icecream import ic
import json
import time
from bson import ObjectId

from errors import SettingsError,BadInputError,AIError
from tools import _ensure_model,cosine_similarity
from schemes.aiSchemes import RecordCreate,RecordEdit,QuestionReponse
from schemes.companySchemes import CompanyScheme,CompanyStructureListItem,CompanyStructureListItemDB,CompanyStructureSetupScheme,ContactPerson,DispenseDepartment
from schemes.knowledgeBaseSchemes import KnowledgeSchemeCreate,MainCategoriesCreate,MainCategoryConfig,MainCategoriesTemplate,MainCategoriesUpdateScheme,KnowledgeFilter
from schemes.userSchemes import UserLoginScheme,UserRegisterScheme,UserRegisterPasswordPresetScheme
from .userModel import User
from .knowledgeModel import KnowledgeBase
from tools import trace


class AI():

    def __init__(self,request:Request):
        db = request.app.state.db
        self.collection = db.chat_history
        self.request=request
        self.user_stamp=None
        
        self.agent=request.app.state.agent
        
        if 'login' in self.request.session:
            self.user_stamp=self.request.session['login']
            if not self.user_stamp:
                raise AIError("Not logged in")
        else:
            
            raise AIError("Not logged in")

    @trace
    async def create_record(self, record_type:str,data:RecordCreate ):
        data.type=record_type
        data=_ensure_model(data,RecordCreate)
        
        person_doc=await User(self.request).get_user({"username":data.user})
        if not person_doc:
            raise BadInputError("user not exist")
        
        data.department=person_doc['department']
        data.company=person_doc['company']
        
        
        data_dict = data.model_dump()
        result=await self.collection.insert_one(data_dict)
        return result.inserted_id

    @trace
    async def edit_record(self,id, data:RecordEdit):
        data=_ensure_model(data,RecordEdit)
        data_dict = data.model_dump(exclude_unset=True,exclude_none=True)
        ic(data_dict)
        ic(ObjectId(id))
        return await self.collection.update_one({"_id":ObjectId(id)},{"$set":data_dict})
    @trace
    async def suggesting(self,prompt,by,instructions=""):
        result=await self.ask_ai(instructions+prompt,"suggesting",by)
        return result[0]
    @trace
    async def chat(self,prompt,by,instructions=""):
        result= await self.ask_ai(instructions+prompt,"chat",by)
        return result [0]
    @trace
    async def auto_tagging(self,categories:list[str],data,by,extend:bool=False,count=1,instructions=""):
        extend_bool={True:"允許",False:"不允許"}[extend]
        
        prompt = f"""
        請你幫我針對以下的內容進行分類：
        目前所有的分類：{categories}。
        需要進行分類的內容：{data}。
        是否允許創建新的分類：{extend_bool}
        請幫我思考目標內容與現有分類的關係，然後從中挑選{count}個最合適的分類進行回覆。
        注意：回覆的時候直接回覆那個分類名稱即可，不要有任何多餘的文字和標點符號！

        以下是範例：
        ——————————————————
        目前所有的分類：["品質管理","倉儲管理","生產管理","客戶服務","採購管理","設備維護","能源管理","物流與配送","研發與創新","財務管理","人力資源","數據安全與治理"]。
        需要進行分類的內容：今天賣出去的商品客戶反應有問題欸要怎麼處理。
        挑選分類數：1
        你的回應：品質管理
        ——————————————————
        目前所有的分類：["品質管理","倉儲管理","生產管理","客戶服務","採購管理","設備維護","能源管理","物流與配送","研發與創新","財務管理","人力資源","數據安全與治理"]。
        需要進行分類的內容：今天賣出去的商品客戶反應有問題欸要怎麼處理。
        挑選分類數：2
        你的回應：品質管理,客戶服務
        """
        return await self.ask_ai(prompt,"auto-tagging",by)[0]
    @trace
    async def make_response(self,question,background,relevant,topn=10):
        prompt = f"""
        【任務說明】
        你的任務是根據「使用者的問題」、「匹配到的相關知識」與「使用者背景資訊」，從中選出最相關的知識條目，並進行回覆。

        【輸出格式】
        請只輸出一行內容，格式如下：

        <knowledge_id>,<answer>

        - 如果有找到與問題相關的知識，請輸出該條目的 `_id`，第二段輸出 `None`
        - 如果找不到任何相關知識，第一段請填 `-1`，第二段請根據使用者背景與同業經驗給出合理建議
        - 請使用 **英文半形逗號（`,`）** 分隔，**不得有空格或空行**

        【使用者問題】
        {question}

        【前 {topn} 筆相關知識（含 _id 與內容）】
        {relevant}

        【使用者背景資訊】
        {background}

        【請依照格式進行輸出】
        範例：
        - 問題：有關教育訓練的 SOP 是什麼？
        - 資料庫內無相關文件
        - 背景資訊顯示公司為大型零售企業

        輸出應為：
        -1,同業通常會在入職後第一週安排產品知識與系統操作訓練，搭配 mentor 協助熟悉環境並建立服務流程標準。
                
        注意：回覆的時候請符合上面說明的格式，不要有任何多餘的文字和標點符號，也不要有任何的空行！格式錯誤會導致系統失敗，請務必遵守格式要求！
        """
        by=self.user_stamp
        return await self.ask_ai(prompt,"chat",by)
    @trace
    async def ask_ai(self,prompt,type,by):
        by=self.user_stamp
        message=f"""
你是我們公司最專業的人工智慧助手，請確保回覆具備專業性、可靠性與準確度。
        
        {prompt}
        """
        
        if type not in ['chat','auto-tagging','suggesting']:
            raise BadInputError("ai record type error")
        
        import time
        start_time = time.time()
        resp = await self.agent.responses.create(
            model="gpt-5-nano-2025-08-07",
            #40s
        #gpt-4.1-2025-04-14
            # gpt-5-nano-2025-08-07
            input=message,
        )
        end_time = time.time()  
        elapsed_seconds = end_time - start_time
        temp_record=RecordCreate(
            ask=message,
            answer=resp.output_text,
            user=by['username'],
            type=type,
            elapse_time=f"{elapsed_seconds}s"
        )
        ic(temp_record)
        id= await  self.create_record(type,temp_record)
        return [resp.output_text,id]
    @trace
    async def generate_background_data(self,background,type="str"):
        filtered_key_map={
            "company_name":"公司名稱",
            "company_type":"公司類型",
            "company_property":"公司特性",
            "company_description":"產業說明",
        }
        background_dict={}
        for i in filtered_key_map:
            background_dict[filtered_key_map[i]]=background[i]
        if type=="str":
            return json.dumps(background_dict, ensure_ascii=False, indent=2).replace("{","").replace("}","").replace("\"","").replace("\'","")
        else:
            return background_dict
    @trace
    async def generate_knowlege(self,background,topic:dict,user_profile,count=10):
        background_dict=await self.generate_background_data(background)
        topic_dict=json.dumps(topic, ensure_ascii=False, indent=2).replace("{","").replace("}","").replace("\"","").replace("\'","")
        ic(background_dict)
        ic(topic)
        
        knowledge_ids = []
        try:
            # for i in topic:
            prompt=f'''
                幫我根據以下關於使用者以及其公司的相關背景知識和產業型態特性等，為每一個主構面生成{count}個範例問題，以及其屬於的子構面。
                這邊需要生成的問題主要是該公司的員工最有可能或是最常見的問題。
                子構面的部分可以選擇沒有出現過的，但是不要新增和已經存在的子構面過於相近的子構面。
                格式說明：每一行的問題分成三個部分，每一個部分用|進行分割，每一行的開頭和結尾也有|
                例如：|問題|子構面|主構面|
                
                背景知識：
                {background_dict}
                主構面和子構面的對應關係：
                {topic_dict}
                
                以下是範例：
                ——————————————————
                背景知識：
                公司名稱: 寶雅國際股份有限公司,
                公司類型: 上櫃公司（Retail 零售通路商）,
                公司特性: 美妝生活雜貨專賣店；產品涵蓋彩妝、保養、流行內衣袜、生活日常用品與精緻個人用品；主要客群為年輕女性；全台分店眾多；線上＋實體通路並行,
                產業說明: 居家生活／生活日常用品零售業。寶雅除了販售歐美、日韓流行彩妝與保養品，也有內衣襪與精緻個人用品，為台灣美妝生活雜貨專賣通路領導品牌之一。
                主構面和子構面的對應關係：
                財務管理:[現金與收銀管理]
                每一個主構面生成5個範例問題
                
                你的回應：
                |每日營收結帳流程為何？|現金與收銀管理|財務管理
                |櫃檯短溢收處理流程為何？|現金與收銀管理|財務管理
                |收銀機異常斷電怎麼辦？|現金與收銀管理|財務管理
                |櫃檯是否可以備有私人物品？|現金與收銀管理|財務管理
                |是否可使用非指定銀行存現？|現金與收銀管理|財務管理
                
                注意：回覆的時候請符合上面說明的格式，不要有任何多餘的文字和標點符號，也不要有任何的空行！格式錯誤會導致系統失敗，請務必遵守格式要求！確保回答的個數也要符合要求
            '''
            result_string = await self.suggesting(prompt,user_profile)
            ic(result_string)
                # 將 AI 回傳內容轉為 list of (question, sub_category, main_category)
            lines = [line.strip('|') for line in result_string.strip().split('\n') if line.strip()]
            qa_list = [line.split('|') for line in lines if len(line.split('|')) == 3]
            
            ic(len(qa_list))
            if len(qa_list)!=count*len(topic):
                raise AIError("Result count generated not expected!")

            for q, sub, main in qa_list:
                embed=await self.embedding(q.strip(),user_profile)
                temp=KnowledgeSchemeCreate(
                    example_question=q.strip(),
                    main_category=main.strip(),
                    sub_category=sub.strip(),
                    created_by=user_profile['username'],
                    company=user_profile["company"],
                    department=user_profile['department'],
                    embedding_example_question=embed
                    
                )
                id=await KnowledgeBase(self.request).create_knowledge(temp)
                knowledge_ids.append(id)

            ic(knowledge_ids)
            return knowledge_ids
        except:
            for id in knowledge_ids:
                await KnowledgeBase(self.request).delete_knowledge(id)
            ic("cleared")
            raise AIError("Result count generated not expected!")
    @trace
    async def embedding(self,content:str,by):
        start_time = time.time()
        response = await self.agent.embeddings.create(
            input=content,
            model="text-embedding-3-small"
        )
        end_time = time.time()  
        elapsed_seconds=end_time-start_time
        data=response.data[0].embedding
        ic(len(data))
        temp_record=RecordCreate(
            ask="",
            answer=str(data),
            user=by['username'],
            type="embedding",
            elapse_time=f"{elapsed_seconds}s"
        )
        await self.create_record("embedding",temp_record)
        return response.data[0].embedding
    #幫我實作
    @trace
    async def vector_search(self,content:str,main_categories:list[str],topn=10):
        by=self.user_stamp
        vector=await self.embedding(content,by)
        knowledges=await KnowledgeBase(self.request).get_knowledge(KnowledgeFilter(main_category=main_categories),True)
        data=[]
        for knowledge in knowledges:
            similarity=cosine_similarity(vector,knowledge['embedding_example_question'])
            data.append((similarity,knowledge['example_question'],str(knowledge['_id']),knowledge['example_answer']))
        
        data.sort(reverse=True, key=lambda x: x[0])
        ic(data[:topn])
        return data[:topn]
            
    @trace
    async def generate_chat_answer(self,company_profile,main_category:str,question:str):
        relevant=await self.vector_search(question,main_category,3)
        background=await self.generate_background_data(company_profile)
        result= await self.make_response(question,background,relevant=relevant)
        
        if ','not in result[0]:
            raise AIError("generate_chat_answer format error")
        else:
            result_list = result[0].split(',')
            if result_list[1] == "None":
                ic(result_list[0])
                doc = await KnowledgeBase(self.request).get_knowledge(KnowledgeFilter(_id=result_list[0]))
                if not doc :
                    raise AIError("Bad id generated")
                await self.edit_record(result[1],RecordEdit(
                    linked_knowledge_id=result_list[0],
                    main_category=doc['main_category'],
                    sub_category=doc['sub_category']))
                print("save id into record")
                ic(doc[0]['example_question'],doc[0]['example_answer'])
                final_result = doc[0]['example_answer']
                
            else:
                
                final_result = result_list[1]
            ic(final_result)
            return final_result
                