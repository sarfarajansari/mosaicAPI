"""
Article Generator

This script generates AI-focused articles by:
1. Picking a topic from a predefined list
2. Using Tavily to search for information about the topic
3. Generating a 700-word article based on the search results
4. Storing the article in MongoDB
"""
import random
import datetime
import hashlib
import logging
from typing import Dict, Any, List, Optional

import pymongo
from pymongo import MongoClient
from langchain_openai import AzureChatOpenAI
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import (
    MONGODB_SRC_URI,
    MONGODB_MOSAIC_DATABASE,
    MONGODB_SCRAPPER_COLLECTION,
    TAVILY_API_KEY,
    get_primary_llm,
    get_tavily_search
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("article-generator")

# Default topics to choose from
from batch_scraper import DEFAULT_TOPICS

def select_random_topic() -> str:
    """Select a random topic from the DEFAULT_TOPICS list."""
    return random.choice(DEFAULT_TOPICS)

def search_for_topic(topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for information about a topic using Tavily.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of search results to return
        
    Returns:
        List of search results
    """
    logger.info(f"Searching for topic: {topic}")
    
    try:
        # Initialize Tavily search
        tavily_search = get_tavily_search()
        
        # Create search query
        search_query = f"latest research and developments in AI: {topic}"
        logger.info(f"Search query: {search_query}")
        
        # Execute search
        search_results = tavily_search.results(search_query, max_results=max_results)
        logger.info(f"Found {len(search_results)} search results")
        
        return search_results
    except Exception as e:
        logger.error(f"Error in search_for_topic: {str(e)}")
        return []

def generate_article(topic: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an article based on the topic and search results.
    
    Args:
        topic: The topic of the article
        search_results: List of search results from Tavily
        
    Returns:
        Dictionary containing the generated article and metadata
    """
    logger.info(f"Generating article for topic: {topic}")
    
    try:
        # Extract content from search results
        contexts = []
        for result in search_results:
            contexts.append(f"Title: {result.get('title', 'No title')}\nURL: {result.get('url', 'No URL')}\nContent: {result.get('content', 'No content')}")
        
        context_text = "\n\n".join(contexts)
        
        # Create prompt for article generation
        template = """
        You are an expert AI journalist writing informative articles about artificial intelligence and technology.
        
        Please create a comprehensive, engaging, and informative article about the following topic:
        
        Topic: {topic}
        
        IMPORTANT INSTRUCTIONS:
        1. The article MUST be EXACTLY 700 words in length. Not more, not less.
        2. Write content that is factual, informative, and based on the search results provided.
        3. Cover the latest developments, applications, and implications of this AI technology or concept.
        
        Use the following information from recent searches to inform your article:
        
        {context}
        
        Your article should have:
        1. A clear and engaging title (not included in the word count)
        2. A brief introduction explaining the significance of the topic
        3. Several informative body paragraphs with factual information
        4. Discussion of real-world applications and implications
        5. A conclusion with future prospects or challenges
        
        Format your response as:
        Title: [Your Title Here]
        
        [Your 700-word article text here]
        
        Remember, aim for EXACTLY 700 words for the article body.
        """
        
        # Initialize LLM - Azure model doesn't support temperature parameter
        llm = get_primary_llm()
        
        # Create and run the generation chain
        prompt = ChatPromptTemplate.from_template(template)
        generation_chain = prompt | llm | StrOutputParser()
        
        article_text = generation_chain.invoke({
            "topic": topic,
            "context": context_text
        })
        
        # Extract title (assuming it's formatted as "Title: ...")
        lines = article_text.strip().split('\n')
        title = ""
        article_body = article_text
        
        for i, line in enumerate(lines):
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
                # Remove the title line and any blank lines after it
                article_body = "\n".join(lines[i+1:]).strip()
                break
        
        # If no title found, use first line as title
        if not title:
            if lines:
                title = lines[0].strip('#').strip()
                if len(lines) > 1:
                    article_body = "\n".join(lines[1:]).strip()
        
        # If still no title, use the topic
        if not title:
            title = topic
        
        # Count words
        word_count = len(article_body.split())
        
        # Generate a unique ID for the article
        content_hash = hashlib.md5(f"{topic}_{title}_{datetime.datetime.now()}".encode()).hexdigest()
        
        # Current timestamp for created_at and updated_at fields
        current_time = datetime.datetime.now().isoformat()
        
        # Create article data structure
        article_data = {
            "id": content_hash,
            "source": {
                "platform": "Tavily Search",
                "urls": [result.get("url") for result in search_results],
                "scrape_timestamp": datetime.datetime.now().isoformat()
            },
            "metadata": {
                "title": title,
                "topic": topic,
                "generation_date": datetime.datetime.now().isoformat(),
                "word_count": word_count,
                "target_length": 700,
                "created_at": current_time,
                "updated_at": current_time
            },
            "content": {
                "article_text": article_body,
                "search_results": search_results
            }
        }
        
        return article_data
    except Exception as e:
        logger.error(f"Error generating article: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        current_time = datetime.datetime.now().isoformat()
        
        return {
            "id": hashlib.md5(f"{topic}_error_{datetime.datetime.now()}".encode()).hexdigest(),
            "metadata": {
                "title": f"Error: {topic}",
                "topic": topic,
                "generation_date": datetime.datetime.now().isoformat(),
                "created_at": current_time,
                "updated_at": current_time
            },
            "error": str(e)
        }

def store_in_mongodb(article_data: Dict[str, Any]) -> bool:
    """
    Store the generated article in MongoDB.
    
    Args:
        article_data: The article data to store
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Storing article in MongoDB: {article_data.get('metadata', {}).get('title', 'No title')}")
    
    try:
        # Initialize MongoDB client
        client = MongoClient(MONGODB_SRC_URI)
        db = client[MONGODB_MOSAIC_DATABASE]
        collection = db[MONGODB_SCRAPPER_COLLECTION]
        
        # Insert the article
        result = collection.insert_one(article_data)
        
        logger.info(f"Article stored with ID: {result.inserted_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing article in MongoDB: {str(e)}")
        return False

def generate_and_store_article(topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate and store an article about AI.
    
    Args:
        topic: Optional specific topic. If None, a random topic will be selected.
        
    Returns:
        Dictionary with information about the process and article
    """
    # Select topic if not provided
    if topic is None:
        topic = select_random_topic()
    
    logger.info(f"Generating article for topic: {topic}")
    
    try:
        # Search for information
        search_results = search_for_topic(topic)
        
        if not search_results:
            return {
                "status": "failed",
                "error": "No search results found",
                "topic": topic
            }
        
        # Generate article
        article_data = generate_article(topic, search_results)
        
        # Store in MongoDB
        stored = store_in_mongodb(article_data)
        
        return {
            "status": "success" if stored else "storage_failed",
            "topic": topic,
            "article_id": article_data.get("id"),
            "title": article_data.get("metadata", {}).get("title"),
            "word_count": article_data.get("metadata", {}).get("word_count")
        }
    except Exception as e:
        logger.error(f"Error in generate_and_store_article: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "failed",
            "error": str(e),
            "topic": topic
        }

def main():
    """Main entry point for the article generator."""
    print("\n==== AI Article Generator ====")
    print("Generating a new article...")
    
    result = generate_and_store_article()
    
    print("\n==== Generation Results ====")
    print(f"Status: {result['status']}")
    print(f"Topic: {result['topic']}")
    
    if result['status'] == 'success':
        print(f"Title: {result.get('title')}")
        print(f"Word count: {result.get('word_count')}")
        print(f"Article ID: {result.get('article_id')}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("============================\n")
    
    return 0 if result['status'] == 'success' else 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 