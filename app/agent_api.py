import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi import FastAPI
from pydantic import BaseModel

import time
import os
from perception import extract_perception
from memory import MemoryManager, MemoryItem
from decision import generate_plan
from action import execute_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from contextlib import asynccontextmanager

class AgentState:
    session = None
    tools = []
    memory = None
    tool_descriptions = ""
    session_id = None

agent_state = AgentState()



@asynccontextmanager
async def lifespan(app: FastAPI):
    server_params = StdioServerParameters(
        command="python",
        args=["example3.py"]
    )
    mcp_initialized = False
    try:
        try:
            async with stdio_client(server_params) as (read, write):
                #agent_state.read = read
                #agent_state.write = write
                async with ClientSession(read, write) as session:
                    #agent_state.session = session
                    tools_result = await session.list_tools()
                    print("hi", tools_result)
                    agent_state.tools = tools_result.tools
                    agent_state.tool_descriptions = "\n".join(
                        f"- {tool.name}: {getattr(tool, 'description', 'No description')}"
                        for tool in agent_state.tools
                    )
                    agent_state.memory = MemoryManager()
                    agent_state.session_id = f"session-{int(time.time())}"
                    print("[startup] Agent server initialized.")
                    mcp_initialized = True
        except Exception as e:
            import traceback
            print("Exception type:", type(e))
            print("Exception args:", e.args)
            print("Exception repr:", repr(e))
            traceback.print_exc()
            print(f"[startup] Failed to initialize agent server 1: {e}")
        yield  # Always yield so FastAPI server starts, even if MCP fails
    finally:
        if not mcp_initialized:
            print("[startup] MCP not initialized; server is running in degraded mode.")


from web_capture_api import router as web_capture_router

app = FastAPI(lifespan=lifespan)
app.include_router(web_capture_router)

class AgentRequest(BaseModel):
    user_input: str


@app.post("/agent")
async def agent_endpoint(request: AgentRequest):
    result = await run_agent_workflow(
        user_input=request.user_input,
        session=agent_state.session,
        tools=agent_state.tools,
        memory=agent_state.memory,
        tool_descriptions=agent_state.tool_descriptions,
        session_id=agent_state.session_id
    )
    return {"result": result}

async def run_agent_workflow(user_input, session, tools, memory, tool_descriptions, session_id, max_steps=3):
    query = user_input
    step = 0
    while step < max_steps:
        perception = extract_perception(user_input)
        print(f"[perception] Intent: {perception.intent}, Tool hint: {perception.tool_hint}")
        retrieved = memory.retrieve(query=user_input, top_k=3, session_filter=session_id)
        print(f"[memory] Retrieved {len(retrieved)} relevant memories")
        plan = generate_plan(perception, retrieved, tool_descriptions=tool_descriptions)
        print(f"[plan] Plan generated: {plan}")
        if plan.startswith("FINAL_ANSWER:"):
            print(f"[agent] ✅ FINAL RESULT: {plan}")
            return plan
        try:
            result = await execute_tool(session, tools, plan)
            print(f"[tool] {result.tool_name} returned: {result.result}")
            memory.add(MemoryItem(
                text=f"Tool call: {result.tool_name} with {result.arguments}, got: {result.result}",
                type="tool_output",
                tool_name=result.tool_name,
                user_query=user_input,
                tags=[result.tool_name],
                session_id=session_id
            ))
            user_input = f"Original task: {query}\nPrevious output: {result.result}\nWhat should I do next?"
        except Exception as e:
            print(f"[error] Tool execution failed: {e}")
            break
        step += 1
    return "FINAL_ANSWER: [unknown]"
