import hashlib
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.config import get_settings
from app.ai.prompts import SYSTEM_PROMPT, RBAC_ADMIN_NOTE, RBAC_USER_NOTE
from app.ai.tools import sql_query, analyze_data, set_context
from app.models.ai_cache import AICache

settings = get_settings()

def _get_llms():
    """Get a list of configured LLMs prioritized by speed and cost."""
    llms = []

    # Priority 1: Groq (Blazing fast, high free limits)
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            llms.append(ChatGroq(
                model="llama3-groq-70b-8192-tool-use-preview",
                api_key=settings.GROQ_API_KEY,
                temperature=0.2,
            ))
        except Exception as e:
            print(f"Groq Init Error: {e}")

    # Priority 2: Anthropic (Fast, excellent reasoning)
    if settings.ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            llms.append(ChatAnthropic(
                model="claude-3-haiku-20240307",
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2,
            ))
        except Exception as e:
            print(f"Anthropic Init Error: {e}")

    # Priority 3: OpenAI (Industry standard)
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            llms.append(ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
            ))
        except Exception as e:
            print(f"OpenAI Init Error: {e}")

    # Priority 4: Gemini (Resilient models)
    if settings.GEMINI_API_KEY:
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llms.append(ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.2,
                    convert_system_message_to_human=True,
                    max_retries=0, # Fail fast on 429
                ))
            except Exception as e:
                print(f"Gemini Init Error: {e}")

    return llms

async def _get_mock_response(question: str, db: AsyncSession, user_id: int) -> str:
    """A rule-based fallback to answer common questions when AI is unavailable."""
    question = question.lower()
    try:
        if "salary" in question or "paid" in question:
            query = f"SELECT employee_name, salary FROM data_records WHERE user_id = {user_id} ORDER BY salary DESC LIMIT 1"
            res = await db.execute(text(query))
            row = res.fetchone()
            if row:
                return f"Based on my quick scan (Resilience Mode), the highest paid employee is **{row[0]}** with a salary of **${row[1]:,.2f}**."

        if "department" in question or "count" in question:
            query = f"SELECT department, COUNT(*) as count FROM data_records WHERE user_id = {user_id} GROUP BY department"
            res = await db.execute(text(query))
            rows = res.fetchall()
            if rows:
                counts = "\n".join([f"• {r[0]}: {r[1]} employees" for r in rows])
                return f"Here is a summary of employees by department:\n{counts}"

        return "I'm currently in **Resilience Mode** (Mock AI). I can see your data but can't perform complex reasoning right now. Try asking about 'highest salary' or 'department counts'."
    except Exception:
        return "I encountered an error even in Mock Mode. Please check your data."

async def get_cached_response(question: str, user_role: str, db: AsyncSession) -> str:
    """Check if a response for this question and role already exists in cache."""
    q_hash = hashlib.sha256(f"{user_role}:{question}".encode()).hexdigest()
    stmt = select(AICache).where(AICache.question_hash == q_hash)
    result = await db.execute(stmt)
    cache_item = result.scalar_one_or_none()
    return cache_item.answer if cache_item else None

async def set_cached_response(question: str, user_role: str, answer: str, db: AsyncSession):
    """Store a successful AI response in the cache."""
    q_hash = hashlib.sha256(f"{user_role}:{question}".encode()).hexdigest()
    new_cache = AICache(question_hash=q_hash, answer=answer)
    db.add(new_cache)
    await db.commit()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception), # Typically you'd catch specific API errors
    reraise=True
)
async def _run_agent_loop(llm, messages):
    """Run the agent loop with tools and built-in retries."""
    tools = [sql_query, analyze_data]
    llm_with_tools = llm.bind_tools(tools)
    
    current_messages = list(messages)
    max_iterations = 5
    for _ in range(max_iterations):
        response = await llm_with_tools.ainvoke(current_messages)
        current_messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name == "sql_query":
                result = await sql_query.ainvoke(tool_args)
            elif tool_name == "analyze_data":
                result = await analyze_data.ainvoke(tool_args)
            else:
                result = f"Unknown tool: {tool_name}"

            current_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    
    return "I couldn't finish analyzing within the limit. Please try a simpler question."

async def chat_with_agent(question: str, db: AsyncSession, user_id: int, user_role: str) -> str:
    """Run the AI agent using best-practice resilient architecture."""

    # 1. Check Cache
    cached = await get_cached_response(question, user_role, db)
    if cached:
        return f"✨ **Cached Insight**:\n{cached}"

    # 2. Resilience: Support Manual Mock Mode
    if settings.USE_MOCK_AI:
        return await _get_mock_response(question, db, user_id)

    # 3. Execution with Multi-Model Fallback
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rbac_filter = RBAC_ADMIN_NOTE if user_role == "admin" else RBAC_USER_NOTE.format(user_id=user_id)
    system_prompt = SYSTEM_PROMPT.format(
        user_role=user_role, user_id=user_id, current_time=current_time, rbac_filter=rbac_filter
    )
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]

    llms = _get_llms()

    if not llms:
        return (
            "⚠️ AI is not configured. Please set at least one API key "
            "(GROQ, ANTHROPIC, OPENAI, or GEMINI) in the .env file to enable AI features."
        )

    errors = []

    for llm in llms:
        set_context(db, user_id, user_role)
        try:
            answer = await _run_agent_loop(llm, messages)
            # 4. Cache successful result
            await set_cached_response(question, user_role, answer, db)
            return answer
        except Exception as e:
            provider_name = llm.__class__.__name__.replace("Chat", "")
            errors.append(f"{provider_name}: {str(e)}")
            continue

    # 5. Final Fallback: Mock Engine
    mock_answer = await _get_mock_response(question, db, user_id)
    error_summary = "\n".join([f"- {err}" for err in errors])
    
    return (
        f"🛡️ **Enterprise Resilience Activation**: All AI providers encountered issues or hit quota limits.\n"
        f"**Diagnostics**:\n{error_summary}\n\n"
        f"**Instant Data Answer**:\n{mock_answer}\n\n"
        f"*Full AI capabilities will restore shortly.*"
    )
