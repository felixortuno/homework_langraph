import json
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from game_state import GameState

# Define the system prompt with the RPG engine persona
SYSTEM_PROMPT = """Actúa como un motor de juego de RPG de texto para el aprendizaje de idiomas.
Tu objetivo es sumergir al usuario en una narrativa dinámica donde el progreso depende de su precisión lingüística.

Configuración del Juego:
1. Estado del Mundo: Mantén un registro persistente del inventario, ubicación, salud y nivel de idioma del jugador.
2. Evaluación Crítica: Antes de generar la respuesta del narrador, analiza la entrada del usuario. Si hay errores gramaticales graves, el PNJ (personaje no jugador) no debe entender al usuario, resultando en una pérdida de "puntos de respeto" o salud. Explica el error brevemente de forma pedagógica.
3. Generación de Misiones: Crea objetivos dinámicos que obliguen al usuario a usar vocabulario nuevo acorde a su nivel.

Formato de Salida:
Devuelve SIEMPRE una respuesta estructurada en JSON válido con los siguientes campos:
- "escena_narrativa": La descripción de la siguiente escena o respuesta del PNJ.
- "evaluacion_linguistica": Feedback sobre la gramática y vocabulario del usuario.
- "cambio_en_estado": Un objeto con los cambios a aplicar (p.ej., {"salud": -10, "inventario": ["+manzana"]}).
- "mision_actual": El objetivo actual del jugador.

Asegúrate de que el JSON sea puramente JSON, sin bloques de código markdown alrededor.
"""

def game_node(state: GameState):
    """
    The main node that processes the game state and user input using the LLM.
    """
    # Initialize the LLM
    # Note: We assume OPENAI_API_KEY is set in the environment.
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    # Construct the context from the state
    context_str = f"""
    Contexto Actual:
    - Idioma Objetivo: {state.get("target_language", "Japanese")}
    - Ubicación: {state.get("location", "Tokyo Market")}
    - Salud: {state.get("health", 100)}
    - Inventario: {state.get("inventory", [])}
    - Nivel: {state.get("language_level", "Beginner")}
    - Misión: {state.get("mission", "Explorar")}
    """

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=context_str),
    ]
    
    # Add history
    messages.extend(state.get("history", []))

    # Invoke the LLM
    response = llm.invoke(messages)
    
    # Parse the response
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        game_data = json.loads(content)
        
        # Update state based on the response
        changes = game_data.get("cambio_en_estado", {})
        
        # Update health
        if "salud" in changes:
            state["health"] = state.get("health", 100) + changes["salud"]
            
        # Update inventory
        if "inventario" in changes:
            current_inv = state.get("inventory", [])
            for item in changes["inventario"]:
                if item.startswith("+"):
                    current_inv.append(item[1:])
                elif item.startswith("-"):
                    item_name = item[1:]
                    if item_name in current_inv:
                        current_inv.remove(item_name)
            state["inventory"] = current_inv
            
        # Update other fields
        state["location"] = game_data.get("ubicacion", state.get("location")) # Optional update if LLM suggests move
        state["mission"] = game_data.get("mision_actual", state.get("mission"))
        state["linguistic_evaluation"] = game_data.get("evaluacion_linguistica")
        
        # Append the assistant's response to history (narrative only to keep context clean-ish, 
        # or full JSON? Better to append the narrative or a summary to history).
        # For this implementation, we'll append the narrative.
        narrative = game_data.get("escena_narrativa", "")
        
        # We need to return the updated state keys
        return {
            "inventory": state["inventory"],
            "health": state["health"],
            "mission": state["mission"],
            "linguistic_evaluation": state["linguistic_evaluation"],
            "history": [response], # LangGraph appends this to the history list
            # We treat the narrative as the response to show to the user, but we store it in history
        }

    except json.JSONDecodeError:
        # Fallback if JSON fails
        return {
            "linguistic_evaluation": "Error parsing LLM response.",
            "history": [response]
        }
