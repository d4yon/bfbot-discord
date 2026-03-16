from langchain_ollama import ChatOllama
import asyncio

MAX_PARALLEL = 4

class LLM:
    def __init__(self):
        self.llm = ChatOllama(model="ministral-3:latest") 
        
        self.semaphore = asyncio.Semaphore(MAX_PARALLEL)

    async def ask(self, history):
        async with self.semaphore:
            return await self.llm.ainvoke(history)