import os


import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])  # async client

async def main():
    # Instruct-style completion (short by default unless you set max_tokens)
    resp = await client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="講個笑話",
        max_tokens=200,           # ✅ increase allowed output length (default is small)
        temperature=0.8,
        stop=None,
    )
    # Print the first choice's text content
    print(resp.choices[0].text.strip())

    # --- Optional: chat-completions variant ---
    # If you prefer the chat endpoint (often better maintained), uncomment below:
    # chat = await client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": "講個笑話"}],
    #     max_tokens=200,
    # )
    # print(chat.choices[0].message.content)

asyncio.run(main())
 