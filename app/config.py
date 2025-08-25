import os

class ConfigManager:
    """
    A centralized manager for application configuration.
    Reads settings from environment variables and provides them to the app.
    """
    def __init__(self):
        print("--- Initializing ConfigManager ---")
        self.MOCK_OLLAMA = os.getenv("MOCK_OLLAMA", "false").lower() == "true"
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3")
        self.OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

        if self.MOCK_OLLAMA:
            print("!!! Ollama mocking is enabled. !!!")
        else:
            print(f"Ollama Base URL: {self.OLLAMA_BASE_URL}")
            print(f"Ollama Chat Model: {self.OLLAMA_CHAT_MODEL}")
            print(f"Ollama Embed Model: {self.OLLAMA_EMBED_MODEL}")

# Create a single, globally accessible instance of the ConfigManager
config = ConfigManager()
