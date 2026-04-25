from google import genai
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='oi',
    )
    print("SUCCESS 2.5:", response.text)
except Exception as e:
    print("ERROR 2.5:", e)

try:
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents='oi',
    )
    print("SUCCESS 1.5:", response.text)
except Exception as e:
    print("ERROR 1.5:", e)
