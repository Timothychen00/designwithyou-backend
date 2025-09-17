import os


import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])  # async client
data="你覺得我要上幾天班"
count=1
categories=["品質管理","倉儲管理","生產管理","客戶服務","採購管理","設備維護","能源管理","物流與配送","研發與創新","財務管理","人力資源","數據安全與治理"]
instructions="""
你是我們公司最強大的人工智慧，所以接下來的所有回答請保證專業性，以及確認回答的可靠性還有準確度，並且按照要求進行回覆。
"""
prompt = f"""
以下是要求：
——————————————————

請你幫我針對以下的內容進行分類：
目前所有的分類：{categories}。
需要進行分類的內容：{data}。
請幫我思考目標內容與現有分類的關係，然後從中挑選{count}個最合適的分類（必須要是已經存在的分類）進行回覆。
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


async def main():

    resp = await client.responses.create(
        model="gpt-5-nano-2025-08-07",
        input=instructions+prompt
    )

    print(resp.output_text)
    # Print the first choice's text content


    # --- Optional: chat-completions variant ---
    # If you prefer the chat endpoint (often better maintained), uncomment below:
    # chat = await client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": "講個笑話"}],
    #     max_tokens=200,
    # )
    # print(chat.choices[0].message.content)

asyncio.run(main())