from fastapi import FastAPI
from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import InMemorySaver

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage

from agents import research_agent, python_agent, get_personal_agent
from oauth import router as oauth_router

# FastAPI

app = FastAPI(
    title="Multi Agent AI Assistant"
)

app.include_router(oauth_router)

# State

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Only the most recent messages get sent to the LLM each turn. Tool
# results (especially Gmail/Drive content) get added to the shared history
# and would otherwise keep growing every message, eventually going over
# Groq's tokens-per-minute limit.
MAX_HISTORY_MESSAGES = 10

def recent_messages(state):
    return state["messages"][-MAX_HISTORY_MESSAGES:]

# Research node

def research_node(state):

    result = research_agent.invoke({
        "messages": recent_messages(state)
    })

    return {
        "messages": result["messages"]
    }

# Python node

def python_node(state):

    result = python_agent.invoke({
        "messages": recent_messages(state)
    })

    return {
        "messages": result["messages"]
    }

# Personal assistant node

def personal_node(state):

    result = get_personal_agent().invoke({
        "messages": recent_messages(state)
    })

    return {
        "messages": result["messages"]
    }

# Router

def router(state):

    message = state["messages"][-1].content.lower()

    personal_words = [
        "email",
        "gmail",
        "inbox",
        "send a mail",
        "drive",
        "upload",
        "download"
    ]

    python_words = [
        "calculate",
        "python",
        "code",
        "equation",
        "math",
        "percentage"
    ]

    for word in personal_words:

        if word in message:
            return "personal"

    for word in python_words:

        if word in message:
            return "python"

    return "research"

# LangGraph

graph = StateGraph(AgentState)

graph.add_node("research", research_node)
graph.add_node("python", python_node)
graph.add_node("personal", personal_node)

graph.add_conditional_edges(
    START,
    router,
    {
        "research": "research",
        "python": "python",
        "personal": "personal"
    }
)

graph.add_edge("research", END)
graph.add_edge("python", END)
graph.add_edge("personal", END)

memory = InMemorySaver()

agent_graph = graph.compile(checkpointer=memory)


# Request model

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

# API

@app.get("/")
def home():

    return {
        "message": "Multi Agent AI Assistant API is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    result = agent_graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=request.message
                )
            ]
        },
        config={
            "configurable": {
                "thread_id": request.thread_id
            }
        })

    answer = result["messages"][-1].content

    return {
        "answer": answer
    }