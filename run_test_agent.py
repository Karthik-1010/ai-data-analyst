import asyncio
import logging
logging.basicConfig(level=logging.INFO)

from app.database import async_session
from app.ai.agent import chat_with_agent

async def main():
    async with async_session() as db:
        print(await chat_with_agent("What is the highest salary?", db, 1, "admin"))

if __name__ == "__main__":
    asyncio.run(main())
