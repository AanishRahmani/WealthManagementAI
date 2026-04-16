import asyncio
from app.core.llm import get_llm
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    agent = create_agent(get_llm(), [])
    messages = [SystemMessage(content="Hello"), HumanMessage(content="Say hi back")]
    res = await agent.ainvoke({"messages": messages})
    print("OUTPUT FORMAT:", type(res), res)
    if isinstance(res, dict) and "messages" in res:
        print("LAST MSG CONTENT:", res["messages"][-1].content)

asyncio.run(main())
