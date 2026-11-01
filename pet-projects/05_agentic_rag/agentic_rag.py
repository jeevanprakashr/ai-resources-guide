from typing import TypedDict, Annotated, Sequence
import operator

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

tool_belt = [DuckDuckGoSearchRun(), ArxivQueryRun()]
tool_node = ToolNode(tool_belt)

model = ChatOllama(
    model="llama3.2:latest",
    validate_model_on_init=True,
    temperature=0.8,
    num_predict=256,
)
# model.bind_tools([convert_to_openai_tool(tool) for tool in tool_belt])
model = model.bind_tools(tool_belt)

def call_model(state: AgentState) -> AgentState:
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

def call_tool(state: AgentState) -> AgentState:
    return tool_node.invoke(state)

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
# workflow.add_node("action", call_tool)
workflow.add_node("action", tool_node)
print()
print(workflow.nodes)
print()

workflow.set_entry_point("agent")

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    return "end"

workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
workflow.add_edge("action", "agent")

app = workflow.compile()
print(app)
print()

inputs: AgentState = {"messages" : [HumanMessage(content="What is RAG in the context of Large Language Models? When did it break onto the scene?")]}
inputs: AgentState = {"messages" : [HumanMessage(content="What is uTHCD defined in the research paper 2103.07676?")]}

response = app.invoke(inputs)
for message in response["messages"]:
    print([message])
    print()


# messages = [HumanMessage(content="What is RAG in the context of Large Language Models? When did it break onto the scene?")]
# response = model.invoke(messages)
# res = [response]
# print(res)