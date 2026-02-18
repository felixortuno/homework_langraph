import os
import sys
from langchain_core.messages import HumanMessage
from graph import app
import json

def main():
    print("Welcome to the London RPG Adventure!")
    print("Initializing game...")

    # Check for API Key
    if "GOOGLE_API_KEY" not in os.environ:
        api_key = input("Please enter your Google API Key: ").strip()
        if not api_key:
            print("API Key determines your fate. Exiting.")
            sys.exit(1)
        os.environ["GOOGLE_API_KEY"] = api_key

    # Initial State
    initial_state = {
        "inventory": ["Oyster Card", "Umbrella"],
        "location": "King's Cross Station",
        "health": 100,
        "respect": 100,
        "language_level": "Beginner",
        "target_language": "English",
        "mission": "Exit the station and find a pub.",
        "history": [],
        "linguistic_evaluation": None
    }
    
    print(f"\nLocation: {initial_state['location']}")
    print(f"Mission: {initial_state['mission']}")
    print("-" * 50)
    
    current_state = initial_state
    
    def parse_and_display(message_content):
        try:
            if message_content.startswith("```json"):
                message_content = message_content[7:-3].strip()
            elif message_content.startswith("```"):
                message_content = message_content[3:-3].strip()
            data = json.loads(message_content)
            
            # Display based on new JSON structure
            if data.get("descripcion_escena"):
                print(f"\n[SCENE]: {data['descripcion_escena']}")
                
            if data.get("dialogo_pnj"):
                print(f"\n[NPC]: {data['dialogo_pnj']}")
            
            if data.get("evaluacion_interna"): # Or maybe this should be hidden or just feedback?
                # User asked for "Evaluación Crítica" explaining errors.
                # "evaluacion_interna" seems to be CoT. 
                # But previous prompt had "evaluacion_linguistica" for feedback.
                # The prompt has "evaluacion_interna" in output.
                # Let's show it as feedback if it contains useful info, or maybe look for specific feedback field?
                # The prompt says: "evaluacion_interna": "Análisis de la gramática..."
                # It doesn't explicitly have a separate user-facing feedback field, but CoT might contain it.
                # Actually, the prompt says NPC reacts to errors.
                # But user *also* asked for "Explica el error brevemente de forma pedagógica" in the first request,
                # and in this request: "Tu objetivo es gestionar la historia mientras actúas como un nodo de control de calidad lingüística."
                # The JSON output in this request is: { "evaluacion_interna": "...", "dialogo_pnj": "...", "descripcion_escena": "...", "actualizacion_estado": ... }
                # The "evaluacion_interna" might be the CoT.
                # Let's decide to show it as [THOUGHTS/FEEDBACK] or keep it hidden if it's purely internal.
                # Given it's a language learning app, showing analysis is helpful.
                print(f"\n[LINGUISTIC ANALYSIS]: {data['evaluacion_interna']}")

            updates = data.get("actualizacion_estado", {})
            if "salud" in updates and updates["salud"] != 0:
                print(f"[STATUS] Health change: {updates['salud']}")
            if "respeto" in updates and updates["respeto"] != 0:
                print(f"[STATUS] Respect change: {updates['respeto']}")
            
            return data
        except json.JSONDecodeError:
            print(f"\n[RAW]: {message_content}")
            return {}

    # First turn to generate initial scene
    result = app.invoke(current_state)
    last_ai_msg = result['history'][-1]
    parse_and_display(last_ai_msg.content)

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            graph_input = {"history": [HumanMessage(content=user_input)]}
            
            result = app.invoke(graph_input)
            
            # Get latest response
            last_ai_msg = result['history'][-1]
            data = parse_and_display(last_ai_msg.content)
            
            # Check game over conditions
            if "health" in result and result["health"] <= 0:
                print("\n[GAME OVER] You collapsed.")
                break
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
