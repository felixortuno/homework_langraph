import json
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from game_state import GameState
import os

# Define the system prompt with the RPG engine persona
SYSTEM_PROMPT = """Actúa como el motor narrativo y evaluador de un RPG de texto para aprender inglés, ambientado en un Londres contemporáneo y realista.
Tu objetivo es gestionar la historia mientras actúas como un nodo de control de calidad lingüística.

Instrucciones de Configuración:
1. Ambiente y Tono: Describe las escenas con detalles icónicos de Londres (ej. el metro, pubs en Camden, el Támesis). El tono debe ser inmersivo pero claro.
2. Evaluación con Cadena de Pensamiento (CoT): Antes de responder a la acción del usuario, analiza internamente:
   - ¿Es la gramática y el vocabulario correctos para un nivel [Nivel de Usuario]?
   - Si hay errores, el PNJ (personaje no jugador) debe reaccionar con confusión o corregir sutilmente al usuario dentro del diálogo. Solo si el error es crítico, el usuario pierde "puntos de respeto" o salud.
3. Gestión de Estado Persistente: Cada respuesta debe considerar el inventario (ej. tarjeta Oyster, paraguas), la ubicación actual y la misión activa.

Formato de Salida Obligatorio (JSON):
Devuelve SIEMPRE un objeto JSON válido con esta estructura:
{
  "evaluacion_interna": "Análisis de la gramática y vocabulario del usuario...",
  "dialogo_pnj": "Lo que dice el personaje...",
  "descripcion_escena": "Narración del entorno...",
  "actualizacion_estado": {
    "salud": X, (cambio relativo, ej. -10 o 0)
    "respeto": X, (cambio relativo, ej. -5 o +5)
    "ubicacion": "...", (si cambia)
    "inventario": ["+item", "-item"], (opcional)
    "mision_actual": "..." (opcional, si cambia)
  }
}
Asegúrate de que el JSON sea puramente JSON, sin bloques de código markdown alrededor.
"""

def game_node(state: GameState):
    """
    The main node that processes the game state and user input using the LLM.
    """
    # Initialize the LLM
    # Using Gemini 1.5 Flash or Pro as standard
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GOOGLE_API_KEY not found in environment.")
        
    # Trying stable high-performance model
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)

    # Construct the context from the state
    context_str = f"""
    Contexto Actual:
    - Idioma Objetivo: {state.get("target_language", "English")}
    - Ubicación: {state.get("location", "King's Cross Station")}
    - Salud: {state.get("health", 100)}
    - Respeto: {state.get("respect", 100)}
    - Inventario: {state.get("inventory", [])}
    - Nivel: {state.get("language_level", "Beginner")}
    - Misión: {state.get("mission", "Exit the station")}
    """

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=context_str),
    ]
    
    # Add history
    current_history = state.get("history", [])
    if not current_history:
        messages.append(HumanMessage(content="Start the game."))
    else:
        messages.extend(current_history)

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
        changes = game_data.get("actualizacion_estado", {})
        
        # Update health
        if "salud" in changes:
            state["health"] = state.get("health", 100) + changes["salud"]
            
        # Update respect
        if "respeto" in changes:
            state["respect"] = state.get("respect", 100) + changes["respeto"]
            
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
        state["location"] = changes.get("ubicacion", state.get("location"))
        state["mission"] = changes.get("mision_actual", state.get("mission"))
        state["linguistic_evaluation"] = game_data.get("evaluacion_interna")
        
        # In this new format, narrative is split between "dialogo_pnj" and "descripcion_escena"
        # We can combine them for the history/display or just return the raw JSON for the UI to handle.
        # Since we are storing the raw AI message in history (handled by LangGraph), we don't change that.
        # But we verify the keys exist.
        
        return {
            "inventory": state["inventory"],
            "health": state["health"],
            "respect": state["respect"],
            "location": state["location"],
            "mission": state["mission"],
            "linguistic_evaluation": state["linguistic_evaluation"],
            "history": [response], 
        }

    except json.JSONDecodeError:
        # Fallback if JSON fails
        return {
            "linguistic_evaluation": "Error parsing LLM response.",
            "history": [response]
        }
