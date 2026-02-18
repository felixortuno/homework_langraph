from langgraph.graph import StateGraph, END
from game_state import GameState
from rpg_node import game_node

# Define the graph
workflow = StateGraph(GameState)

# Add the node
workflow.add_node("game_master", game_node)

# Set the entry point
workflow.set_entry_point("game_master")

# Add edge to end (this is a single-step graph per turn, the loop handles the recursion in main)
workflow.add_edge("game_master", END)

# Compile the graph
app = workflow.compile()
