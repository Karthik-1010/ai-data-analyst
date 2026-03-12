import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

async def test_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key or key.startswith("sk-..."):
        print("OpenAI key is missing or truncated in .env")
        return False
    
    print(f"Testing OpenAI with key: {key[:5]}...{key[-4:]}")
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=key, temperature=0, max_retries=0)
        res = await llm.ainvoke("Hi, just say 'Ready'")
        print(f"SUCCESS: OpenAI - Response: {res.content}")
        return True
    except Exception as e:
        print(f"FAILED: OpenAI - Error: {e}")
        return False

async def test_gemini(model_name):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("Gemini API Key not found")
        return False

    print(f"Testing {model_name}...")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=key,
            temperature=0,
            max_retries=0
        )
        res = await llm.ainvoke("Hi, just say 'Ready'")
        print(f"SUCCESS: {model_name} - Response: {res.content}")
        return True
    except Exception as e:
        print(f"FAILED: {model_name} - Error: {e}")
        return False

async def main():
    print("--- Testing OpenAI ---")
    await test_openai()
    
    print("\n--- Testing Gemini ---")
    models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    for m in models:
        await test_gemini(m)

if __name__ == "__main__":
    asyncio.run(main())
