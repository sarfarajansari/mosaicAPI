import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGODB_SRC_URI = os.getenv("MONGODB_SRC_URI")
MONGODB_MOSAIC_DATABASE = os.getenv("MONGODB_MOSIAC_DATABASE")
MONGODB_SCRAPPER_COLLECTION = os.getenv("MONGODB_SCRAPPER_COLLECTION")

# Tavily API Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY_O3_mini")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT_O3_mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION_O3_mini")
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME_O3_mini")

# Firecrawl API Configuration
# Note: Add Firecrawl API key and endpoint once available
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_API_ENDPOINT = os.getenv("FIRECRAWL_API_ENDPOINT", "https://api.firecrawl.dev/crawl")

# Debug configuration loading
def debug_config():
    """Print configuration values for debugging."""
    print("\n==== Configuration ====")
    print(f"MongoDB URI: {'Set' if MONGODB_SRC_URI else 'NOT SET'}")
    print(f"MongoDB Database: {MONGODB_MOSAIC_DATABASE}")
    print(f"MongoDB Collection: {MONGODB_SCRAPPER_COLLECTION}")
    print(f"Tavily API Key: {'Set' if TAVILY_API_KEY else 'NOT SET'}")
    print(f"Azure OpenAI API Key: {'Set' if AZURE_OPENAI_API_KEY else 'NOT SET'}")
    print(f"Azure OpenAI Endpoint: {'Set' if AZURE_OPENAI_ENDPOINT else 'NOT SET'}")
    print("=======================\n")

# Function to get Tavily search
def get_tavily_search():
    """Get a configured Tavily search wrapper."""
    from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
    return TavilySearchAPIWrapper(tavily_api_key=TAVILY_API_KEY)

# Function to get primary LLM
def get_primary_llm(temperature=None):
    """Get the primary LLM for content generation."""
    from langchain_openai import AzureChatOpenAI
    
    # Azure OpenAI models don't support temperature parameter
    model_params = {
        "openai_api_version": AZURE_OPENAI_API_VERSION,
        "azure_deployment": AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
    }
    
    return AzureChatOpenAI(**model_params)

# Function to get a lightweight LLM for utilities
def get_o3_mini_llm(temperature=None):
    """Get the O3 Mini LLM for utility tasks."""
    from langchain_openai import AzureChatOpenAI
    
    # Azure OpenAI models don't support temperature parameter
    model_params = {
        "openai_api_version": AZURE_OPENAI_API_VERSION,
        "azure_deployment": AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
    }
    
    return AzureChatOpenAI(**model_params) 