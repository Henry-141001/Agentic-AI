from fastapi import FastAPI
from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import InMemorySaver

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage

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
    last_agent: str

# Only the most recent messages get sent to the LLM each turn. Tool
# results (especially Gmail/Drive content) get added to the shared history
# and would otherwise keep growing every message, eventually going over
# Groq's tokens-per-minute limit.
MAX_HISTORY_MESSAGES = 10

def recent_messages(state):
    return state["messages"][-MAX_HISTORY_MESSAGES:]

# Any node can hit a third-party hiccup - a search engine timing out, an
# API rate limit, a Google API error. Without this, one bad tool call
# crashes the whole /chat request. This turns that into a normal chat
# reply instead, so the conversation can just continue.
def safe_invoke(agent, state, agent_name):

    try:

        result = agent.invoke({
            "messages": recent_messages(state)
        })

        return {
            "messages": result["messages"],
            "last_agent": agent_name
        }

    except Exception as error:

        return {
            "messages": [AIMessage(
                content=f"Something went wrong handling that ({error}). Please try again."
            )],
            "last_agent": agent_name
        }

# Research node

def research_node(state):
    return safe_invoke(research_agent, state, "research")

# Python node

def python_node(state):
    return safe_invoke(python_agent, state, "python")

# Personal assistant node

def personal_node(state):
    return safe_invoke(get_personal_agent(), state, "personal")

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

    # No clear keyword this time - if we're mid-conversation with an
    # agent, stay with it instead of jumping back to research. A message
    # like "date before august 2026" only makes sense as a follow-up to
    # whichever agent was just talking.
    if state.get("last_agent"):
        return state["last_agent"]

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