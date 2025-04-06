"""
Batch Article Generator

This script generates multiple AI-focused articles in batch by:
1. Taking a number of articles to generate
2. For each article:
   a. Picking a topic from the predefined list
   b. Using Tavily to search for information
   c. Generating a 700-word article
   d. Storing it in MongoDB
"""
import argparse
import logging
import time
import json
from typing import List, Dict, Any
import random

from article_generator import generate_and_store_article, DEFAULT_TOPICS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("batch-article-generator")

def run_batch_generator(
    num_articles: int = 5,
    topics: List[str] = None,
    delay_between_articles: int = 5,
    output_file: str = None
) -> Dict[str, Any]:
    """
    Generate multiple articles in batch.
    
    Args:
        num_articles: Number of articles to generate
        topics: List of topics to use (if None, random topics will be selected)
        delay_between_articles: Delay in seconds between article generation
        output_file: Optional file to write results to
        
    Returns:
        Dictionary with batch results
    """
    logger.info(f"Starting batch generator for {num_articles} articles")
    
    results = []
    successful_articles = 0
    failed_articles = 0
    
    # Select topics if not provided
    if topics is None:
        if num_articles <= len(DEFAULT_TOPICS):
            # Choose random subset of topics without replacement
            topics = random.sample(DEFAULT_TOPICS, num_articles)
        else:
            # If we need more topics than available, allow repeats
            topics = [random.choice(DEFAULT_TOPICS) for _ in range(num_articles)]
    
    # Process each article
    for i, topic in enumerate(topics):
        logger.info(f"Processing article {i+1}/{num_articles}: {topic}")
        
        try:
            # Generate and store the article
            result = generate_and_store_article(topic)
            
            # Add to results
            results.append({
                "topic": topic,
                "status": result.get("status"),
                "title": result.get("title"),
                "article_id": result.get("article_id"),
                "word_count": result.get("word_count"),
                "error": result.get("error")
            })
            
            # Update stats
            if result.get("status") == "success":
                successful_articles += 1
            else:
                failed_articles += 1
                logger.error(f"Failed to process article for topic: {topic}")
                if result.get("error"):
                    logger.error(f"Error: {result.get('error')}")
            
            # Log progress
            logger.info(f"Article {i+1}/{num_articles} completed")
            logger.info(f"Progress: {successful_articles}/{num_articles} articles successful")
            
            # Delay between articles to avoid rate limiting
            if i < len(topics) - 1:
                logger.info(f"Waiting {delay_between_articles} seconds before next article...")
                time.sleep(delay_between_articles)
                
        except Exception as e:
            logger.error(f"Error processing article for topic {topic}: {str(e)}")
            failed_articles += 1
            import traceback
            logger.error(traceback.format_exc())
            
            # Add failed result
            results.append({
                "topic": topic,
                "status": "failed",
                "error": str(e)
            })
    
    # Compile overall results
    batch_result = {
        "total_articles": num_articles,
        "successful_articles": successful_articles,
        "failed_articles": failed_articles,
        "results": results
    }
    
    # Write results to file if specified
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(batch_result, f, indent=2)
            logger.info(f"Results written to {output_file}")
        except Exception as e:
            logger.error(f"Error writing results to file: {str(e)}")
    
    logger.info(f"Batch processing completed:")
    logger.info(f"Articles: {successful_articles}/{num_articles} successful")
    
    return batch_result

def main():
    """Main entry point for the batch article generator."""
    parser = argparse.ArgumentParser(description="Batch AI Article Generator")
    parser.add_argument("--articles", type=int, default=5, 
                        help="Number of articles to generate (default: 5)")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay in seconds between articles (default: 5)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file for batch results")
    parser.add_argument("--topics-file", type=str, default=None,
                        help="JSON file containing list of topics to process")
    
    args = parser.parse_args()
    
    # Print welcome message
    print(f"\n==== Batch AI Article Generator ====")
    print(f"Number of articles: {args.articles}")
    print(f"Delay between articles: {args.delay} seconds")
    if args.output:
        print(f"Output file: {args.output}")
    print("=====================================\n")
    
    # Get topics if specified
    topics = None
    if args.topics_file:
        try:
            with open(args.topics_file, 'r') as f:
                topics = json.load(f)
            print(f"Loaded {len(topics)} topics from {args.topics_file}")
        except Exception as e:
            print(f"Error loading topics from file: {str(e)}")
            print(f"Using random topics instead")
    
    # Run the batch generator
    result = run_batch_generator(
        num_articles=args.articles,
        topics=topics,
        delay_between_articles=args.delay,
        output_file=args.output
    )
    
    # Print summary
    print("\n==== Batch Generation Results ====")
    print(f"Articles processed: {result['total_articles']}")
    print(f"Articles successful: {result['successful_articles']}")
    print(f"Articles failed: {result['failed_articles']}")
    print("===================================\n")
    
    # Return appropriate exit code
    if result['failed_articles'] == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 