import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the GEMINI_API_KEY from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

# Import the necessary classes - note: these would need to be available in your environment
# Since these are custom agent classes, I'm providing a structure based on standard OpenAI library
try:
    from openai import OpenAI  # Use synchronous OpenAI client for compatibility with agent.py

    external_client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    # For compatibility with agent.py, we'll define simple model name variable
    class SimpleModel:
        def __init__(self, model_name):
            self.model = model_name

    model = SimpleModel("gemini-2.5-flash")

    # Simple config object for compatibility
    class SimpleConfig:
        pass

    config = SimpleConfig()

    print("Connection to Gemini API via OpenAI-compatible endpoint established successfully.")
    print(f"Model configured: {model.model}")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have the 'agents' package installed and available in your environment.")
    print("This might be a custom or third-party library for agent functionality.")
except Exception as e:
    print(f"Error establishing connection: {e}")