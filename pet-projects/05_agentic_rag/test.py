from typing import TypedDict, Annotated, Sequence, get_type_hints
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph

class AgentState(TypedDict):
  messages: Annotated[Sequence[int], operator.add]

d: AgentState = {"messages": [1, 2, 3]}
e: AgentState = {"messages": [4, 5, 6]}

