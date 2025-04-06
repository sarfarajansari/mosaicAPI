# AI Article Generator

A system that automatically generates AI-focused articles by:
1. Selecting topics from a predefined list
2. Using Tavily Search API to research the topic
3. Generating a 700-word article using an LLM
4. Storing the article in MongoDB

## Setup

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Configure your environment variables by creating a `.env` file with:
   ```
   # MongoDB Configuration
   MONGODB_SRC_URI=your_mongodb_connection_string
   MONGODB_MOSIAC_DATABASE=mosaic
   MONGODB_SCRAPPER_COLLECTION=ScrapedData

   # Tavily API
   TAVILY_API_KEY=your_tavily_api_key

   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY_O3_mini=your_azure_openai_api_key
   AZURE_OPENAI_ENDPOINT_O3_mini=your_azure_openai_endpoint
   AZURE_OPENAI_API_VERSION_O3_mini=2024-12-01-preview
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME_O3_mini=o3-mini
   ```

3. Test your environment setup:
   ```
   python run.py --dry-run
   ```
   This will check if all required environment variables are set correctly.

## Usage

### Simple Interface (Recommended)

Use the `run.py` script as a simple interface to the system:

```
# Generate a single article with a random topic
python run.py

# Generate a single article with a specific topic
python run.py --topic "AI in Healthcare"

# Generate multiple articles in batch mode
python run.py --batch --articles 5 --delay 5

# Generate articles from a specific list of topics
python run.py --batch --topics-file my_topics.json --output results.json

# Check environment setup without generating articles
python run.py --dry-run
```

Options:
- `--batch`: Run in batch mode to generate multiple articles
- `--articles`: Number of articles to generate in batch mode (default: 5)
- `--delay`: Delay in seconds between articles in batch mode (default: 5)
- `--output`: Output file for batch results (JSON)
- `--topic`: Specific topic for single article generation
- `--topics-file`: JSON file containing list of topics to process in batch mode
- `--dry-run`: Check environment setup without generating articles

### Alternative Usage

#### Generate a single article

```
python article_generator.py
```

#### Generate multiple articles in batch

```
python batch_article_generator.py --articles 5 --delay 5
```

## System Components

- `run.py`: Simple interface for running the system
- `article_generator.py`: Core module for generating and storing articles
- `batch_article_generator.py`: Batch processing of multiple articles
- `config.py`: Configuration for API keys and services
- `batch_scraper.py`: Contains the list of AI topics

## Predefined Topics

The system includes a wide range of predefined AI topics organized into categories:
- AI in Specific Industries
- Ethical and Social Implications
- Emerging Technologies and Trends
- AI Applications and Innovations
- AI for Global Challenges
- Creative and Cultural Aspects

## Article Structure

Each generated article includes:
- A clear and engaging title
- An introduction explaining the significance of the topic
- Factual information in an organized manner
- Discussion of real-world applications and implications
- Conclusion with future prospects or challenges

## MongoDB Storage

Articles are stored in MongoDB with the following structure:
- `id`: Unique identifier hash
- `source`: Information about the sources used
- `metadata`: Article metadata (title, topic, generation date, word count)
- `content`: The full article text and search results used

## Requirements

- Python 3.8+
- MongoDB database
- Tavily API key
- Azure OpenAI access 