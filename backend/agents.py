import os

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent

from tools import research_tools, python_tools, get_personal_tools

load_dotenv()

# LangSmith tracing (only turns on if a key is present in .env)

if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "Multi-Agent AI Assistant")

# LLM

llm = ChatGroq(model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7)

# Research Agent

research_agent = create_agent(
    llm,
    tools=research_tools,
    system_prompt="""
    You are a Research Agent.

You handle:
- Web searches
- Current information
- News
- Wikipedia questions
- Weather questions

Use the appropriate tool whenever necessary.

Give a clear and concise answer.
    """)

# Python Agent

python_agent = create_agent(
    llm,
    tools=python_tools,
    system_prompt="""
    You are a Python Agent.

You handle:
- Mathematical calculations
- Python programming
- Data calculations
- Small Python experiments

Use the Python tool whenever useful.

Give a clear answer.
    """
)

# Personal Assistant Agent
#
# Built fresh on every call instead of once at startup, since the Gmail
# tools only exist after the user logs in through /auth/login - which
# happens after the server has already started.

PERSONAL_AGENT_PROMPT = """
You are a Personal Assistant Agent.

You may ONLY use tools that are explicitly given to you in this
conversation. Never invent a tool name (for example, there is no tool
simply called "gmail") and never call a tool with a "method" argument -
each real tool already does one specific job and takes its own named
arguments.

Your real Gmail tools, if connected, are named exactly:
- search_gmail - find emails matching a search query
- get_gmail_message - read one specific email by id
- get_gmail_thread - read a whole email thread by id
- send_gmail_message - send a new email
- create_gmail_draft - create a draft without sending it

Your real Google Drive tools are named exactly:
- list_drive_files - list files in Drive
- upload_file - upload a file from a local path to Drive

Always ask for missing details (like recipient, subject, or file path)
instead of guessing.

If no Gmail tools are available to you, tell the user to connect their
Google account by visiting /auth/login on this backend.

Give a clear and concise answer.
"""


def get_personal_agent():

    return create_agent(
        llm,
        tools=get_personal_tools(),
        system_prompt=PERSONAL_AGENT_PROMPT
    )