# Language Learning RPG Engine

Welcome to the text-based RPG for language learning! This game uses LangGraph and OpenAI to create a dynamic story where your progress depends on your language skills.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **API Key**:
    You need an OpenAI API Key. You can set it as an environment variable or enter it when prompted.
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

## How to Play

Run the game with:

```bash
python main.py
```

The game starts in **Tokyo Market** helping you practice **Japanese**.
- The Narrator describes the scene.
- You type your response/action in the console.
- The default language level is **Beginner**.

## Features

- **Inventory System**: You can pick up items (e.g., "+apple" in the narrative logic).
- **Health System**: Grammatical errors may reduce your health (respect points).
- **Missions**: The game generates missions for you to complete.

## Customization

To change the target language or starting location, edit `main.py`:

```python
    initial_state = {
        # ...
        "location": "Mercado en Tokio",
        "target_language": "Japonés",
        # ...
    }
```
