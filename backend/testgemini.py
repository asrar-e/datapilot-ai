import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

model = os.getenv("GEMINI_MODEL")

print(f"Testing model: {model}")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.interactions.create(
    model=model,
    input="Reply with exactly: Gemini connection successful"
)

print(response.output_text)