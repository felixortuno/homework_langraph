import streamlit as st
import os
import json
from langchain_core.messages import HumanMessage
from graph import app

# Page config
st.set_page_config(page_title="London RPG Adventure", page_icon="🇬🇧", layout="wide")

# Styling
st.markdown("""
<style>
    .stChatInput {
        position: fixed;
        bottom: 0px;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🇬🇧 London RPG Adventure")
    
    # Sidebar for Game State
    with st.sidebar:
        st.header("Player Status")
        
        # API Key handling
        if "GOOGLE_API_KEY" not in os.environ:
            api_key = st.text_input("Google API Key", type="password")
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key
                st.success("API Key set!")
            else:
                st.warning("Please enter your Google API Key to start.")
                st.stop()
        
        if "game_state" in st.session_state:
            state = st.session_state.game_state
            
            c1, c2 = st.columns(2)
            c1.metric("Health", f"{state.get('health', 100)}%")
            c2.metric("Respect", f"{state.get('respect', 100)}")
            
            st.divider()
            
            st.subheader("📍 Location")
            st.info(state.get("location", "Unknown"))
            
            st.subheader("🎯 Mission")
            st.warning(state.get("mission", "None"))
            
            st.subheader("🎒 Inventory")
            inventory = state.get("inventory", [])
            if inventory:
                for item in inventory:
                    st.write(f"- {item}")
            else:
                st.write("Empty")
                
            st.divider()
            
            if st.button("Restart Game"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "game_state" not in st.session_state:
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
        st.session_state.game_state = initial_state
        
        # Trigger first message
        with st.spinner("Initializing game world..."):
            try:
                result = app.invoke(initial_state)
                # Store the updated state
                # Note: Result contains the full state dict returned by the graph
                # We need to preserve the session
                
                # The graph returns the final state.
                # However, history in result is a list of messages.
                # We should extract the last message from AI.
                
                last_msg = result['history'][-1]
                content = last_msg.content
                
                # Parse JSON
                try:
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    data = json.loads(content)
                    
                    narrative = data.get("descripcion_escena", "")
                    npc_dialogue = data.get("dialogo_pnj", "")
                    analysis = data.get("evaluacion_interna", "")
                    
                    # Construct initial message
                    full_msg = ""
                    if narrative:
                        full_msg += f"**[SCENE]** {narrative}\n\n"
                    if npc_dialogue:
                        full_msg += f"**[NPC]** \"{npc_dialogue}\"\n\n"
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_msg, "analysis": analysis})
                    
                    # Update local state
                    st.session_state.game_state = result
                    
                except json.JSONDecodeError:
                    st.session_state.messages.append({"role": "assistant", "content": content})
                    
            except Exception as e:
                st.error(f"Error starting game: {e}")

    # Display Chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "analysis" in msg and msg["analysis"]:
                with st.expander("Linguistic Analysis"):
                    st.info(msg["analysis"])

    # User Input
    if prompt := st.chat_input("What do you do?"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Process with AI
        with st.spinner(" The Narrator is thinking..."):
            try:
                # Prepare input for graph
                # We need to pass the *current state* plus the new message
                current_state = st.session_state.game_state
                
                # We can't just pass the state dict directly if the graph expects "history" update
                # Or we invoke with the state dict updating history?
                # app.invoke(state) uses the state.
                # If we modify the state history here
                
                # Actually, in LangGraph, we typically pass the input as a dict with the keys to update.
                # `history` uses `add_messages`.
                graph_input = {"history": [HumanMessage(content=prompt)]}
                
                # We must also ensure other state keys are available if the node needs them?
                # No, LangGraph passes the current state from checkpoint if we use checkpointer, 
                # but here we are using `StateGraph` without persistence checkpointer, just passing state manually?
                # Wait, if we provided `current_state` to `invoke`, it replaces/merges?
                # If we compiled without checkpointer, `invoke(input, config)` expects input.
                # If input is partial, it merges?
                # Actually, `app.invoke(input)`: input is the starting state.
                # So we must pass the FULL state if we aren't using a checkpointer.
                
                # So update current_state with the new message
                # But wait, `history` in `GameState` is `Annotated[List, add_messages]`.
                # If we pass full list, it might duplicate?
                # No, if we pass the state dict, we should pass the CURRENT state including history?
                # If we pass full history + new message?
                
                # Let's try passing the full state but with appended history.
                # OR, better:
                # Since we don't have a checkpointer, we need to pass the full state object every time.
                # The state returned by `invoke` is the new full state.
                # So `st.session_state.game_state` holds the full state from the last turn.
                
                # We need to add the user message to history before invoking?
                # Or let the graph handle it?
                # The graph input schema is `GameState`.
                # If we pass `{"history": [msg], ...other_keys}` it should work.
                
                # Construct state to pass
                state_to_pass = st.session_state.game_state.copy()
                # We append the user message to history?
                # If `add_messages` is used, passing a list adds to existing?
                # But here we are passing the state dictionary explicitly.
                # If we pass the *same* history list, it might be fine if we are not using checkpointer.
                # Actually, without checkpointer, the state is just what we pass in.
                # So we must append the user message to `history` in the dict we pass.
                
                state_to_pass["history"].append(HumanMessage(content=prompt))
                
                result = app.invoke(state_to_pass)
                
                # Update Session State
                st.session_state.game_state = result
                
                # Extract AI response
                last_msg = result['history'][-1]
                content = last_msg.content
                
                # Parse JSON
                try:
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    data = json.loads(content)
                    
                    narrative = data.get("descripcion_escena", "")
                    npc_dialogue = data.get("dialogo_pnj", "")
                    analysis = data.get("evaluacion_interna", "")
                    
                    full_msg = ""
                    if narrative:
                        full_msg += f"**[SCENE]** {narrative}\n\n"
                    if npc_dialogue:
                        full_msg += f"**[NPC]** \"{npc_dialogue}\"\n\n"
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_msg, "analysis": analysis})
                    
                except json.JSONDecodeError:
                    st.session_state.messages.append({"role": "assistant", "content": content})
                    
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
