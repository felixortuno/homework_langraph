
import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from game_state import GameState
from rpg_node import game_node
import json

class TestRPGNode(unittest.TestCase):
    def setUp(self):
        self.initial_state: GameState = {
            "inventory": ["Oyster Card"],
            "location": "King's Cross Station",
            "health": 100,
            "respect": 100,
            "language_level": "Beginner",
            "history": [],
            "mission": "Exit the station",
            "target_language": "English",
            "linguistic_evaluation": None
        }
        # Mock env var for testing
        import os
        os.environ["GOOGLE_API_KEY"] = "fake_key"

    @patch("rpg_node.ChatGoogleGenerativeAI")
    def test_game_node_success(self, mock_chat):
        # Setup mock LLM response
        mock_llm_instance = MagicMock()
        mock_chat.return_value = mock_llm_instance
        
        expected_json = {
            "descripcion_escena": "You see the bustling platform.",
            "dialogo_pnj": "Mind the gap!",
            "evaluacion_interna": "Correct usage.",
            "actualizacion_estado": {
                "salud": 0, 
                "respeto": 5,
                "ubicacion": "Platform 9 3/4",
                "inventario": ["+ticket"]
            }
        }
        mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps(expected_json))
        
        # Test input message
        # In reality, history would contain user input
        self.initial_state["history"] = [HumanMessage(content="I look for the platform")]
        
        # Run node
        result = game_node(self.initial_state)
        
        # Verify result structure
        self.assertIn("inventory", result)
        self.assertIn("respect", result)
        self.assertIn("health", result)
        
        # Verify updates
        self.assertEqual(result["inventory"], ["Oyster Card", "ticket"])
        self.assertEqual(result["respect"], 105)
        self.assertEqual(result["location"], "Platform 9 3/4")
        
    @patch("rpg_node.ChatGoogleGenerativeAI")
    def test_game_node_damage(self, mock_chat):
        mock_llm_instance = MagicMock()
        mock_chat.return_value = mock_llm_instance
        
        expected_json = {
            "descripcion_escena": "The guard looks confused.",
            "dialogo_pnj": "Sorry?",
            "evaluacion_interna": "Incorrect grammar.",
            "actualizacion_estado": {
                "respeto": -10,
                "salud": -5
            }
        }
        mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps(expected_json))
        
        result = game_node(self.initial_state)
        
        self.assertEqual(result["health"], 95)
        self.assertEqual(result["respect"], 90)

if __name__ == "__main__":
    unittest.main()
