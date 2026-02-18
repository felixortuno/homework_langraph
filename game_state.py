from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GameState(TypedDict):
    """
    Represents the state of the RPG game.
    """
    inventory: List[str]
    location: str
    health: int
    language_level: str
    history: Annotated[List[BaseMessage], add_messages]
    mission: str
    target_language: str
    linguistic_evaluation: Optional[str]
