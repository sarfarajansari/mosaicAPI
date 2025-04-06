# AI Discovery Platform

An intelligent platform for discovering, categorizing, and summarizing AI tools, models, and research papers, with personalized digest generation capabilities.

## Features

- **Multi-source Scraping**: Aggregate AI data from web searches (Tavily, Firecrawl), GitHub, ArXiv, and other sources
- **Structured Data Extraction**: Extract specific attributes like capabilities, technical specs, and author information
- **MongoDB Integration**: Store all discovered items in a MongoDB database for easy retrieval
- **Modular Architecture**: Use scrapers individually or in combination

## Components

The platform consists of specialized scrapers that can be used individually or combined:

- **Tavily Scraper**: Uses Tavily search API to find AI-related content
- **Firecrawl Scraper**: Leverages Firecrawl for deep web search capabilities
- **Combined Scraper**: Unifies results from multiple search providers

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB database
- API keys for Tavily and Firecrawl

### Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Create a `.env` file with your configuration:
```
# MongoDB Configuration
MONGODB_SRC_URI=mongodb+srv://your-connection-string
MONGODB_SCRAPPER_DATABASE=ScrapedData

# API Keys
TAVILY_API_KEY=your-tavily-api-key
FIRECRAWL_API_KEY=your-firecrawl-api-key

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY_O3_mini=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT_O3_mini=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION_O3_mini=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME_O3_mini=o3-mini

# LLM Configuration
LLM_TEMPERATURE=0.1
```

### Usage

The system provides a unified command-line interface through `main.py`:

```bash
# Basic usage with Tavily
python main.py tavily --query "large language models"

# Using Firecrawl with output file
python main.py firecrawl --query "AI image generation" --output results.json

# Using both search providers with limited results
python main.py combined --query "transformer models" --max-results 5

# View MongoDB statistics
python main.py stats
```

### Individual Scrapers

You can also run individual scrapers directly:

```bash
# Tavily Scraper
python tavily_scraper.py --query "multimodal models" --max-results 10

# Firecrawl Scraper
python firecrawl_scraper.py --query "AI for video generation" --output video_ai.json
```

## Project Structure

```
.
├── main.py                  # Main CLI entry point
├── scraper_config.py        # Shared configuration settings
├── scraper_utils.py         # Common utility functions
├── tavily_scraper.py        # Tavily-based web scraper
├── firecrawl_scraper.py     # Firecrawl-based web scraper
├── combined_scraper.py      # Combined search approach
├── Scraping_agents.py       # LangGraph-based scraping agent
├── github_scraper.py        # GitHub repository scraper
├── arxiv_scraper.py         # ArXiv research paper scraper
└── requirements.txt         # Python dependencies
```

## Data Schema

All scraped items are stored in a consistent MongoDB schema:

```json
{
  "id": "unique-identifier",
  "metadata": {
    "title": "AI Tool/Model Name",
    "type": "model/library/framework/service",
    "authors": ["Author 1", "Author 2"],
    "published_date": "2023-01-01",
    "description": "Detailed description of the AI tool or model"
  },
  "content": {
    "capabilities": ["capability1", "capability2"],
    "technical_specs": {
      "models": ["model1", "model2"],
      "languages": ["Python", "JavaScript"],
      "hardware_requirements": "Description of hardware needs"
    },
    "code_snippets": [
      {
        "language": "python",
        "code": "print('Hello world')"
      }
    ],
    "images": ["url1", "url2"],
    "repository_link": "https://github.com/user/repo",
    "paper_link": "https://arxiv.org/abs/XXXX.XXXXX"
  },
  "source": {
    "url": "https://original-source-url.com",
    "platform": "github/arxiv/web/huggingface",
    "scrape_timestamp": "2023-04-15T14:32:10Z",
    "scraper_id": "tavily/firecrawl/combined"
  }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Powered by LangChain and LangGraph
- Uses Azure OpenAI for advanced natural language understanding
- Tavily for intelligent search capabilities 