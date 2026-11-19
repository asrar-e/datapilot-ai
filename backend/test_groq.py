
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

print(f"Testing model: {model}")

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: Groq connection successful"
        }
    ]
)

print(response.choices[0].message.content)
