"""
AI topic scraper workflow using LangGraph.
This workflow searches for AI topics using Tavily, creates articles with an LLM,
and stores the results in MongoDB.
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import uuid
import json
import datetime
import hashlib
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config import (
    MONGODB_SRC_URI,
    MONGODB_MOSAIC_DATABASE,
    MONGODB_SCRAPPER_COLLECTION,
    get_tavily_search,
    get_primary_llm,
    get_o3_mini_llm,
    debug_config
)

# MongoDB Setup
import pymongo
from pymongo import MongoClient

# Initialize MongoDB client
client = MongoClient(MONGODB_SRC_URI)
db = client[MONGODB_MOSAIC_DATABASE]
collection = db[MONGODB_SCRAPPER_COLLECTION]

# Data Models
class ArticleData(BaseModel):
    """Data structure for the scraped article information."""
    id: str = Field(..., description="Unique identifier hash")
    source: Dict[str, Any] = Field(..., description="Source information")
    metadata: Dict[str, Any] = Field(..., description="Article metadata")
    content: Dict[str, Any] = Field(..., description="Article content")
    raw_text: Optional[str] = Field(None, description="Raw text from the search")
    scraper_metadata: Dict[str, Any] = Field(..., description="Scraper metadata")

# State definition for the workflow
class WorkflowState(TypedDict):
    """State for the AI scraper workflow."""
    topic: str
    search_results: Optional[List[Dict[str, Any]]]
    processed_articles: Optional[List[ArticleData]]
    current_article: Optional[ArticleData]
    status: str
    error: Optional[str]
    trace_id: str
    limit: int

def create_ai_scraper_workflow():
    """
    Create a workflow for searching AI topics, generating articles, and storing in MongoDB.
    """
    # Set up logging
    import logging
    logger = logging.getLogger("ai-scraper")
    logger.setLevel(logging.INFO)
    
    # Create a handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.info("Creating AI scraper workflow")
    
    # Define workflow nodes
    def search_for_topic(state: WorkflowState) -> WorkflowState:
        """Search for AI topics using Tavily."""
        topic = state["topic"]
        logger.info(f"Searching for topic: {topic}")
        
        try:
            # Initialize Tavily search
            tavily_search = get_tavily_search()
            
            # Create search query
            search_query = f"latest research and developments in AI: {topic}"
            logger.info(f"Search query: {search_query}")
            
            # Execute search
            search_results = tavily_search.results(search_query)
            logger.info(f"Found {len(search_results)} search results")
            
            # Return updated state
            return {
                **state,
                "search_results": search_results,
                "status": "search_completed"
            }
        except Exception as e:
            logger.error(f"Error in search_for_topic: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                **state,
                "error": f"Search error: {str(e)}",
                "status": "search_failed"
            }
    
    def process_search_results(state: WorkflowState) -> WorkflowState:
        """Process search results and prepare for article generation."""
        search_results = state.get("search_results", [])
        limit = state.get("limit", 5)  # Get the limit from state, default to 5
        
        logger.info(f"Processing {len(search_results)} search results (limiting to {limit})")
        
        # Limit the number of search results to process
        search_results = search_results[:limit]
        
        processed_articles = []
        
        for result in search_results:
            try:
                # Generate unique ID
                result_str = result.get("url", "") + result.get("title", "") + str(datetime.datetime.now())
                unique_id = hashlib.md5(result_str.encode()).hexdigest()
                
                # Create timestamp
                timestamp = datetime.datetime.now().isoformat()
                
                # Extract domain from URL
                url = result.get("url", "")
                import tldextract
                extracted = tldextract.extract(url)
                domain = f"{extracted.domain}.{extracted.suffix}"
                platform = domain
                
                # Create article data structure
                article = ArticleData(
                    id=unique_id,
                    source={
                        "platform": platform,
                        "url": url,
                        "scrape_timestamp": timestamp
                    },
                    metadata={
                        "title": result.get("title", "Untitled"),
                        "authors": [],  # Will be filled by the LLM
                        "published_date": None  # Will be filled by the LLM if available
                    },
                    content={
                        "description": result.get("content", ""),
                        "abstract": "",  # Will be filled by the LLM
                        "article_text": "",  # Will be filled by the LLM
                        "keywords": []  # Will be filled by the LLM
                    },
                    raw_text=result.get("content", ""),
                    scraper_metadata={
                        "agent_version": "1.0.0",
                        "extraction_confidence": 0.8,
                        "errors": []
                    }
                )
                
                processed_articles.append(article)
                logger.info(f"Processed article: {article.metadata['title']} ({article.id})")
                
            except Exception as e:
                logger.error(f"Error processing search result: {str(e)}")
                continue
        
        logger.info(f"Created {len(processed_articles)} article structures")
        
        return {
            **state,
            "processed_articles": processed_articles,
            "current_article": processed_articles[0] if processed_articles else None,
            "status": "results_processed"
        }
    
    def generate_article(state: WorkflowState) -> WorkflowState:
        """Generate an article from the search result using LLM."""
        current_article = state.get("current_article")
        if not current_article:
            logger.error("No current article to process")
            return {
                **state,
                "error": "No article data available for generation",
                "status": "article_generation_failed"
            }
        
        logger.info(f"Generating article for: {current_article.metadata['title']}")
        
        try:
            # Initialize LLM
            llm = get_primary_llm()
            
            # Create prompt for article generation
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                You are an AI research journalist who creates informative articles about artificial intelligence topics.
                Your task is to create a comprehensive article based on the provided source content.
                
                The article should:
                1. Have a clear structure with introduction, body, and conclusion
                2. Extract and infer key information from the source
                3. Be factual and well-researched
                4. Identify potential authors if mentioned in the content
                5. Include relevant keywords for the topic
                6. Be at least 250 words in length - longer articles are preferred
                
                Format your response as a JSON object with the following structure:
                {{
                    "article_text": "Full article text with proper paragraphs",
                    "abstract": "A concise summary of the article (1-2 paragraphs)",
                    "authors": ["Author Name 1", "Author Name 2"],
                    "keywords": ["keyword1", "keyword2", "keyword3"],
                    "published_date": "ISO date string if available, otherwise null"
                }}
                """),
                ("human", """
                Source Title: {title}
                Source URL: {url}
                Source Content: {content}
                
                Based on this information, please generate a comprehensive article of at least 250 words.
                """)
            ])
            
            # Invoke LLM
            chain = prompt | llm | StrOutputParser()
            article_json = chain.invoke({
                "title": current_article.metadata["title"],
                "url": current_article.source["url"],
                "content": current_article.raw_text
            })
            
            # Parse the result
            try:
                # Extract JSON from possible text wrapper
                if "```json" in article_json:
                    article_json = article_json.split("```json")[1].split("```")[0].strip()
                elif "```" in article_json:
                    article_json = article_json.split("```")[1].split("```")[0].strip()
                
                article_data = json.loads(article_json)
                
                # Update article with generated content
                updated_article = current_article.model_copy(deep=True)
                updated_article.content["article_text"] = article_data.get("article_text", "")
                updated_article.content["abstract"] = article_data.get("abstract", "")
                updated_article.metadata["authors"] = article_data.get("authors", [])
                updated_article.content["keywords"] = article_data.get("keywords", [])
                
                if article_data.get("published_date"):
                    updated_article.metadata["published_date"] = article_data.get("published_date")
                
                logger.info(f"Successfully generated article with {len(updated_article.content['article_text'])} characters")
                
                return {
                    **state,
                    "current_article": updated_article,
                    "status": "article_generated"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM output as JSON: {str(e)}")
                logger.error(f"Raw output: {article_json[:200]}...")
                
                # Try to salvage as plain text
                updated_article = current_article.model_copy(deep=True)
                updated_article.content["article_text"] = article_json
                updated_article.scraper_metadata["errors"].append(f"JSON parse error: {str(e)}")
                updated_article.scraper_metadata["extraction_confidence"] = 0.5
                
                return {
                    **state,
                    "current_article": updated_article,
                    "status": "article_generated_with_errors"
                }
                
        except Exception as e:
            logger.error(f"Error in generate_article: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                **state,
                "error": f"Article generation error: {str(e)}",
                "status": "article_generation_failed"
            }
    
    def store_in_mongodb(state: WorkflowState) -> WorkflowState:
        """Store the generated article in MongoDB."""
        current_article = state.get("current_article")
        if not current_article:
            logger.error("No article to store in MongoDB")
            return {
                **state,
                "error": "No article data available for storage",
                "status": "storage_failed"
            }
        
        logger.info(f"Storing article in MongoDB: {current_article.id}")
        
        try:
            # Convert to dictionary
            article_dict = current_article.model_dump()
            
            # Add timestamps
            current_time = datetime.datetime.utcnow().isoformat()
            article_dict["metadata"]["created_at"] = current_time
            article_dict["metadata"]["updated_at"] = current_time
            
            # Insert into MongoDB
            result = collection.insert_one(article_dict)
            
            logger.info(f"Successfully stored article in MongoDB with _id: {result.inserted_id}")
            
            return {
                **state,
                "status": "article_stored"
            }
        except Exception as e:
            logger.error(f"Error storing article in MongoDB: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                **state,
                "error": f"MongoDB storage error: {str(e)}",
                "status": "storage_failed"
            }
    
    def process_next_or_finish(state: WorkflowState) -> str:
        """Determine whether to process the next article or finish."""
        processed_articles = state.get("processed_articles", [])
        current_article = state.get("current_article")
        
        if not processed_articles or not current_article:
            logger.info("No more articles to process, finishing workflow")
            return "finish"
        
        # Find current article index
        try:
            current_index = next(i for i, article in enumerate(processed_articles) 
                              if article.id == current_article.id)
        except StopIteration:
            logger.error("Could not find current article in processed articles")
            return "finish"
        
        # Check if there are more articles to process
        if current_index < len(processed_articles) - 1:
            logger.info(f"Moving to next article ({current_index + 1}/{len(processed_articles)})")
            return "next_article"
        else:
            logger.info("All articles processed, finishing workflow")
            return "finish"
    
    def setup_next_article(state: WorkflowState) -> WorkflowState:
        """Set up the next article for processing."""
        processed_articles = state.get("processed_articles", [])
        current_article = state.get("current_article")
        
        if not processed_articles or not current_article:
            logger.error("No articles available for next setup")
            return {
                **state,
                "error": "No articles available for next setup",
                "status": "setup_failed"
            }
        
        # Find current article index
        try:
            current_index = next(i for i, article in enumerate(processed_articles) 
                              if article.id == current_article.id)
        except StopIteration:
            logger.error("Could not find current article in processed articles")
            return {
                **state,
                "error": "Current article not found in processed articles",
                "status": "setup_failed"
            }
        
        # Set next article as current
        next_index = current_index + 1
        if next_index < len(processed_articles):
            next_article = processed_articles[next_index]
            logger.info(f"Set up next article: {next_article.metadata['title']} ({next_article.id})")
            
            return {
                **state,
                "current_article": next_article,
                "status": "next_article_ready"
            }
        else:
            logger.error("No more articles to process")
            return {
                **state,
                "error": "No more articles to process",
                "status": "setup_failed"
            }
    
    def finish(state: WorkflowState) -> WorkflowState:
        """Finish the workflow and return final state."""
        logger.info("Finishing AI scraper workflow")
        
        # Count successful articles
        processed_articles = state.get("processed_articles", [])
        success_count = len(processed_articles)
        
        logger.info(f"Workflow complete. Processed {success_count} articles")
        
        return {
            **state,
            "status": "completed"
        }
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("search_for_topic", search_for_topic)
    workflow.add_node("process_search_results", process_search_results)
    workflow.add_node("generate_article", generate_article)
    workflow.add_node("store_in_mongodb", store_in_mongodb)
    workflow.add_node("setup_next_article", setup_next_article)
    workflow.add_node("finish", finish)
    
    # Add edges
    workflow.add_edge("search_for_topic", "process_search_results")
    workflow.add_edge("process_search_results", "generate_article")
    workflow.add_edge("generate_article", "store_in_mongodb")
    workflow.add_conditional_edges(
        "store_in_mongodb",
        process_next_or_finish,
        {
            "next_article": "setup_next_article",
            "finish": "finish"
        }
    )
    workflow.add_edge("setup_next_article", "generate_article")
    workflow.add_edge("finish", END)
    
    # Set entry point
    workflow.set_entry_point("search_for_topic")
    
    # Compile workflow
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

def run_ai_scraper(topic: str, limit: int = 5) -> Dict[str, Any]:
    """
    Run the AI scraper workflow for a given topic.
    
    Args:
        topic: The AI topic to search for
        limit: Maximum number of articles to process (default: 5)
        
    Returns:
        Dictionary with workflow results
    """
    # Set up logging
    import logging
    logger = logging.getLogger("ai-scraper")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.info(f"Starting AI scraper workflow for topic: {topic}")
    logger.info(f"Article limit: {limit}")
    
    # Debug configuration
    debug_config()
    
    # Create a trace ID
    trace_id = str(uuid.uuid4())
    logger.info(f"Trace ID: {trace_id}")
    
    # Get the workflow
    workflow = create_ai_scraper_workflow()
    
    # Create initial state
    initial_state = {
        "topic": topic,
        "search_results": None,
        "processed_articles": None,
        "current_article": None,
        "status": "initialized",
        "error": None,
        "trace_id": trace_id,
        "limit": limit
    }
    
    # Run the workflow
    try:
        logger.info("Running workflow...")
        
        # Create config with thread_id for the checkpointer
        config = {"configurable": {"thread_id": trace_id}}
        
        # Invoke workflow with config parameter
        result = workflow.invoke(initial_state, config=config)
        
        logger.info(f"Workflow completed with status: {result['status']}")
        
        # Return summary of results
        processed_articles = result.get("processed_articles", [])
        return {
            "status": result["status"],
            "trace_id": trace_id,
            "articles_processed": len(processed_articles) if processed_articles else 0,
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "workflow_error",
            "trace_id": trace_id,
            "error": str(e)
        }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_scraper_workflow.py <topic>")
        sys.exit(1)
    
    topic = sys.argv[1]
    result = run_ai_scraper(topic)
    
    print(f"AI Scraper completed with status: {result['status']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    print(f"Articles processed: {result.get('articles_processed', 0)}")
    print(f"Trace ID: {result['trace_id']}") 