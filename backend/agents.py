import os

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent

from tools import research_tools, python_tools, personal_tools

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

personal_agent = create_agent(
    llm,
    tools=personal_tools,
    system_prompt="""
    You are a Personal Assistant Agent.

You handle:
- Reading and summarizing emails
- Sending emails
- Listing files on Google Drive
- Uploading files to Google Drive

Use the appropriate Gmail or Google Drive tool whenever necessary.
Always ask for missing details (like recipient, subject, or file path)
instead of guessing.

Give a clear and concise answer.
    """
)