import os
import sys
from langchain_core.messages import HumanMessage
from graph import app

def main():
    print("Welcome to the Language Learning RPG!")
    print("Initializing game...")

    # Check for API Key
    if "OPENAI_API_KEY" not in os.environ:
        api_key = input("Please enter your OpenAI API Key: ").strip()
        if not api_key:
            print("API Key determines your fate. Exiting.")
            sys.exit(1)
        os.environ["OPENAI_API_KEY"] = api_key

    # Initial State
    initial_state = {
        "inventory": [],
        "location": "Mercado en Tokio", # Default as per user request example
        "health": 100,
        "language_level": "Principiante",
        "target_language": "Japonés",
        "mission": "Comprar una manzana",
        "history": [],
        "linguistic_evaluation": None
    }
    
    # Run the initial node to get the opening scene
    # We trigger this by sending an empty message or an initial system trigger
    # But our node expects some history or just runs.
    # Let's seed with a system-like message from the "user" effectively starting the game?
    # Or just invoke with the state.
    
    print(f"\nLocation: {initial_state['location']}")
    print(f"Mission: {initial_state['mission']}")
    print("-" * 50)

    # First turn - let the AI generate the scene based on initial state
    # We treat the first execution as "generating the description"
    # To trigger the LLM to write the first scene, we can add a dummy message or just rely on system prompt + context.
    # The system prompt says "Actúa as...".
    # If history is empty, the LLM should generate the start.
    
    current_state = initial_state
    
    # We use stream to get the output, or invoke.
    # App.invoke(state) returns the final state.
    
    # First specific call to get opening scene
    result = app.invoke(current_state)
    
    # Print opening scene
    last_message = result['history'][-1]
    # The node appends the AI (narrator) response to history.
    # But wait, my node parses JSON and *returns* a dict with history update?
    # No, my node code:
    # returns {"history": [response], ...}
    # result['history'] will hopefully contain the appended message if I used the reducer correctly.
    # Yes, add_messages handles it.
    
    # However, since I return a structured dict from the node, the message is in `history`.
    # But the "content" of the message is the raw JSON string from the LLM.
    # I didn't update the message content to be just the narrative.
    # The LLM output is JSON.
    # So `last_message.content` is JSON.
    # I should parse it for display.
    
    import json
    def parse_and_display(message_content):
        try:
            if message_content.startswith("```json"):
                message_content = message_content[7:-3].strip()
            elif message_content.startswith("```"):
                message_content = message_content[3:-3].strip()
            data = json.loads(message_content)
            print(f"\nNARRATOR: {data.get('escena_narrativa', '')}")
            if data.get('evaluacion_linguistica'):
                print(f"[FEEDBACK]: {data['evaluacion_linguistica']}")
            if data.get('mission_actual'): # The LLM might output "mision_actual"
                print(f"[MISSION]: {data.get('mision_actual')}")
            
            # Print changes if any explicitly for debugging/user info?
            # User only sees narrative and feedback ideally.
            
            return data
        except json.JSONDecodeError:
            print(f"\nNARRATOR: {message_content}")
            return {}

    last_ai_msg = result['history'][-1]
    parse_and_display(last_ai_msg.content)

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Create a HumanMessage
            # We need to manually add this to the state validation or just pass it to invoke.
            # invoke(input) -> input is the state update.
            # So we pass {"history": [HumanMessage(content=user_input)]}
            
            graph_input = {"history": [HumanMessage(content=user_input)]}
            
            result = app.invoke(graph_input)
            
            # Get latest response
            # Since history accumulates, we want the last message which is AI
            last_ai_msg = result['history'][-1]
            data = parse_and_display(last_ai_msg.content)
            
            # Check state updates
            if "salud" in result and result["health"] <= 0:
                print("\n[GAME OVER] Has perdido toda tu salud.")
                break
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
