from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.completions.create(
    model="gpt-3.5-turbo-instruct",  # 取代原本的 text-davinci-003
    prompt="講個笑話來聽聽",
    max_tokens=128,
    temperature=0.5,
)

print(response.choices[0].text)