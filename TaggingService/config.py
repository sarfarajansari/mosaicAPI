import os
from dotenv import load_dotenv

# Load environment variables from .env file in the parent directory or current directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

load_dotenv(dotenv_path=dotenv_path)

# MongoDB Configuration
MONGODB_SRC_URI = os.getenv("MONGODB_SRC_URI")
MONGODB_MOSIAC_DATABASE = os.getenv("MONGODB_MOSIAC_DATABASE")
MONGODB_SCRAPPER_COLLECTION = os.getenv("MONGODB_SCRAPPER_COLLECTION")
MONGODB_DATA_COLLECTION = os.getenv("MONGODB_DATA_COLLECTION")

# Azure OpenAI Configuration (Using the specified GPT-4o keys)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

# --- Optional: Function to get LLM ---
def get_tagging_llm(temperature=0):
    """Get the Azure OpenAI LLM configured for tagging."""
    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME]):
        raise ValueError("Azure OpenAI credentials are not fully configured in the environment variables.")

    from langchain_openai import AzureChatOpenAI

    # Most models including Azure's generally support temperature.
    # If a specific deployment errors, it can be removed.
    model_params = {
        "openai_api_version": AZURE_OPENAI_API_VERSION,
        "azure_deployment": AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
        "temperature": temperature,
        "max_tokens": 1024, # Limit output size for tags
    }

    return AzureChatOpenAI(**model_params)

# Debug configuration loading (optional)
def debug_config():
    """Print configuration values for debugging."""
    print("\\n==== Tagging Service Configuration ====")
    print(f"MongoDB URI: {'Set' if MONGODB_SRC_URI else 'NOT SET'}")
    print(f"MongoDB Database: {MONGODB_MOSIAC_DATABASE}")
    print(f"MongoDB Scraper Collection: {MONGODB_SCRAPPER_COLLECTION}")
    print(f"MongoDB Target Data Collection: {MONGODB_DATA_COLLECTION}")
    print(f"Azure OpenAI API Key: {'Set' if AZURE_OPENAI_API_KEY else 'NOT SET'}")
    print(f"Azure OpenAI Endpoint: {'Set' if AZURE_OPENAI_ENDPOINT else 'NOT SET'}")
    print(f"Azure OpenAI Version: {AZURE_OPENAI_API_VERSION}")
    print(f"Azure OpenAI Deployment: {AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}")
    print("=====================================\\n")

if __name__ == "__main__":
    debug_config() 