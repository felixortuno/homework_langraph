
import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from game_state import GameState
from rpg_node import game_node
import json

class TestRPGNode(unittest.TestCase):
    def setUp(self):
        self.initial_state: GameState = {
            "inventory": [],
            "location": "Tokyo Market",
            "health": 100,
            "language_level": "Beginner",
            "history": [],
            "mission": "Buy an apple",
            "target_language": "Japanese",
            "linguistic_evaluation": None
        }

    @patch("rpg_node.ChatOpenAI")
    def test_game_node_success(self, mock_chat):
        # Setup mock LLM response
        mock_llm_instance = MagicMock()
        mock_chat.return_value = mock_llm_instance
        
        expected_json = {
            "escena_narrativa": "You see a vendor selling apples.",
            "evaluacion_linguistica": "Good job!",
            "cambio_en_estado": {"salud": 0, "inventario": ["+apple"]},
            "mision_actual": "Eat the apple"
        }
        mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps(expected_json))
        
        # Test input message
        # In reality, history would contain user input
        self.initial_state["history"] = [HumanMessage(content="I want apple")]
        
        # Run node
        result = game_node(self.initial_state)
        
        # Verify LLM called
        mock_llm_instance.invoke.assert_called_once()
        
        # Verify result structure
        self.assertIn("inventory", result)
        self.assertIn("mission", result)
        self.assertIn("health", result)
        
        # Verify updates
        self.assertEqual(result["inventory"], ["apple"])
        self.assertEqual(result["mission"], "Eat the apple")
        self.assertEqual(result["health"], 100)
        
        # Verify history appended
        # The node returns a dict with history list update
        # Result "history" should be a list containing the AIMessage
        self.assertEqual(len(result["history"]), 1)
        self.assertIsInstance(result["history"][0], AIMessage)
        self.assertIn("escena_narrativa", result["history"][0].content)

    @patch("rpg_node.ChatOpenAI")
    def test_game_node_damage(self, mock_chat):
        mock_llm_instance = MagicMock()
        mock_chat.return_value = mock_llm_instance
        
        expected_json = {
            "escena_narrativa": "The vendor doesn't understand you.",
            "evaluacion_linguistica": "Grammar error.",
            "cambio_en_estado": {"salud": -10},
            "mision_actual": "Try again"
        }
        mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps(expected_json))
        
        result = game_node(self.initial_state)
        
        self.assertEqual(result["health"], 90)

if __name__ == "__main__":
    unittest.main()
