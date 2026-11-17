import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import tools
import context

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3.5-Super-VL"),
    api_key=os.environ["NEBIUS_API_KEY"],
    base_url="https://api.tokenfactory.us-north1.nebius.com/v1/",
    temperature=0.2,
)

llm_with_tools = llm.bind_tools(
    tools,
    parallel_tool_calls=False,
)

def call_model(state: MessagesState):
    """Send repository context and the conversation to the model."""
    repository_context = context.build_repository_context()
    messages = [
        SystemMessage(
            content=(
                "You are a terminal coding agent. Use the repository context "
                "to understand the workspace before choosing tools.\n\n"
                f"{repository_context}"
            )
        ),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("model", call_model)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition)
builder.add_edge("tools", "model")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

