"""
Batch AI topic scraper workflow.
This script processes multiple AI topics and generates articles for each.
"""
import sys
import argparse
import logging
import time
from typing import List, Dict, Any
import json
from ai_scraper_workflow import run_ai_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("batch-scraper")

# List of AI topics to process
DEFAULT_TOPICS = [
    # AI in Specific Industries
    "The Role of AI in Revolutionizing Healthcare Diagnostics",
    "AI in Education: Personalized Learning and Adaptive Assessments",
    "Artificial Intelligence in Agriculture: Enhancing Crop Management",
    "AI in Finance: Fraud Detection and Risk Management",
    "AI in Transportation: Autonomous Vehicles and Traffic Optimization",
    "AI in Marketing: Personalization and Behavioral Targeting",
    "The Impact of AI on Modern Warfare and Defense Strategies",
    
    # Ethical and Social Implications
    "Ethical Challenges in Artificial Intelligence Development",
    "Addressing Algorithmic Bias in AI Systems",
    "The Future of Work: How AI is Reshaping the Labor Market",
    "Privacy Concerns in the Age of AI-Powered Surveillance",
    "Can Artificial Intelligence Be Fair? Exploring Ethical Algorithms",
    
    # Emerging Technologies and Trends
    "Explainable AI: Bridging the Gap Between Humans and Machines",
    "Quantum Computing and Its Implications for AI Development",
    "Generative AI: From Deepfakes to Creative Content Creation",
    "Edge Computing with AI: Bringing Intelligence to the Edge Devices",
    
    # AI Applications and Innovations
    "Natural Language Processing for Sentiment Analysis on Social Media",
    "Machine Learning in Predictive Analytics for Business Decision-Making",
    "Computer Vision Applications: From Facial Recognition to Autonomous Drones",
    "Reinforcement Learning in Robotics for Real-World Applications",
    
    # AI for Global Challenges
    "Using AI to Predict and Mitigate Climate Change Impacts",
    "AI in Disaster Management: Enhancing Emergency Response Systems",
    "Fighting Fake News with Artificial Intelligence Detection Tools",
    "Smart Cities Powered by AI: Improving Urban Sustainability",
    
    # Creative and Cultural Aspects
    "The Role of AI in Art, Music, and Literature: Creativity Redefined"
]

# Define a test subset of topics for quick testing
TEST_TOPICS = [
    # AI in Specific Industries
    "The Role of AI in Revolutionizing Healthcare Diagnostics",
    # Ethical and Social Implications
    "Ethical Challenges in Artificial Intelligence Development",
    # Emerging Technologies and Trends
    "Generative AI: From Deepfakes to Creative Content Creation",
    # AI Applications and Innovations
    "Natural Language Processing for Sentiment Analysis on Social Media",
    # AI for Global Challenges
    "Smart Cities Powered by AI: Improving Urban Sustainability"
]

def run_batch_scraper(
    topics: List[str] = DEFAULT_TOPICS,
    articles_per_topic: int = 4,
    delay_between_topics: int = 2,
    output_file: str = None
) -> Dict[str, Any]:
    """
    Run the AI scraper for multiple topics.
    
    Args:
        topics: List of topics to process
        articles_per_topic: Number of articles to generate per topic
        delay_between_topics: Delay in seconds between processing topics
        output_file: Optional file to write results to
        
    Returns:
        Dictionary with batch results
    """
    logger.info(f"Starting batch scraper for {len(topics)} topics")
    logger.info(f"Generating {articles_per_topic} articles per topic")
    
    results = []
    total_articles = 0
    successful_topics = 0
    failed_topics = 0
    
    # Process each topic
    for i, topic in enumerate(topics):
        logger.info(f"Processing topic {i+1}/{len(topics)}: {topic}")
        
        try:
            # Run the scraper for this topic
            result = run_ai_scraper(topic, limit=articles_per_topic)
            
            # Add to results
            result["topic"] = topic
            results.append(result)
            
            # Update stats
            articles_processed = result.get("articles_processed", 0)
            total_articles += articles_processed
            
            if result["status"] == "completed" and articles_processed > 0:
                successful_topics += 1
            else:
                failed_topics += 1
                logger.error(f"Failed to process topic: {topic}")
                if result.get("error"):
                    logger.error(f"Error: {result['error']}")
            
            # Log progress
            logger.info(f"Topic {i+1}/{len(topics)} completed with {articles_processed} articles")
            logger.info(f"Progress: {successful_topics}/{len(topics)} topics successful")
            
            # Delay between topics to avoid rate limiting
            if i < len(topics) - 1:
                logger.info(f"Waiting {delay_between_topics} seconds before next topic...")
                time.sleep(delay_between_topics)
                
        except Exception as e:
            logger.error(f"Error processing topic {topic}: {str(e)}")
            failed_topics += 1
            import traceback
            logger.error(traceback.format_exc())
    
    # Compile overall results
    batch_result = {
        "total_topics": len(topics),
        "successful_topics": successful_topics,
        "failed_topics": failed_topics,
        "total_articles": total_articles,
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
    logger.info(f"Topics: {successful_topics}/{len(topics)} successful")
    logger.info(f"Articles: {total_articles} total")
    
    return batch_result

def main():
    """Main entry point for the batch scraper."""
    parser = argparse.ArgumentParser(description="Batch AI Topic Scraper")
    parser.add_argument("--articles", type=int, default=4, 
                        help="Number of articles to generate per topic (default: 4)")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay in seconds between topics (default: 5)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file for batch results")
    parser.add_argument("--topics-file", type=str, default=None,
                        help="JSON file containing list of topics to process")
    parser.add_argument("--min-length", type=int, default=250,
                        help="Minimum word count for generated articles (default: 250)")
    parser.add_argument("--test", action="store_true",
                        help="Use a small subset of topics for testing")
    
    args = parser.parse_args()
    
    # Print welcome message
    print(f"\n==== Batch AI Topic Scraper ====")
    print(f"Articles per topic: {args.articles}")
    print(f"Delay between topics: {args.delay} seconds")
    print(f"Minimum article length: {args.min_length} words")
    if args.output:
        print(f"Output file: {args.output}")
    print("===============================\n")
    
    # Get topics to process
    topics = TEST_TOPICS if args.test else DEFAULT_TOPICS
    
    # If topics file is specified, load from file
    if args.topics_file:
        try:
            with open(args.topics_file, 'r') as f:
                topics = json.load(f)
            print(f"Loaded {len(topics)} topics from {args.topics_file}")
        except Exception as e:
            print(f"Error loading topics from file: {str(e)}")
            print(f"Using {'test' if args.test else 'default'} topics instead")
    
    print(f"Processing {len(topics)} topics...")
    
    # Run the batch scraper
    result = run_batch_scraper(
        topics=topics,
        articles_per_topic=args.articles,
        delay_between_topics=args.delay,
        output_file=args.output
    )
    
    # Print summary
    print("\n==== Batch Scraping Results ====")
    print(f"Topics processed: {result['total_topics']}")
    print(f"Topics successful: {result['successful_topics']}")
    print(f"Topics failed: {result['failed_topics']}")
    print(f"Total articles generated: {result['total_articles']}")
    print("================================\n")
    
    # Return appropriate exit code
    if result['failed_topics'] == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 