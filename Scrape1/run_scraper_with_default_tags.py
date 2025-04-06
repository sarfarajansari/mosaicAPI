"""
Run the AI scraper workflow for multiple default AI topics.
"""
import sys
from ai_scraper_workflow import run_ai_scraper

# Define default AI topics/tags to scrape
DEFAULT_TOPICS = [
    "Large Language Models",
    "Computer Vision",
    "Reinforcement Learning",
    "AI Ethics",
    "Neural Networks",
    "Generative AI",
    "Natural Language Processing",
    "Machine Learning",
    "Robotics",
    "AI Safety"
]

def run_scraper_for_all_default_topics(limit_per_topic=3):
    """
    Run the AI scraper for all default topics.
    
    Args:
        limit_per_topic: Maximum number of articles to process per topic (default: 3)
    """
    print(f"Starting AI scraper for {len(DEFAULT_TOPICS)} default topics")
    print(f"Article limit per topic: {limit_per_topic}")
    
    results = []
    
    for topic in DEFAULT_TOPICS:
        print(f"\n{'='*50}")
        print(f"Processing topic: {topic}")
        print(f"{'='*50}")
        
        result = run_ai_scraper(topic, limit=limit_per_topic)
        
        print(f"Completed topic '{topic}' with status: {result['status']}")
        print(f"Articles processed: {result.get('articles_processed', 0)}")
        
        results.append({
            "topic": topic,
            "status": result["status"],
            "articles_processed": result.get("articles_processed", 0),
            "trace_id": result["trace_id"],
            "error": result.get("error")
        })
    
    # Print summary
    print("\n\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    
    total_articles = sum(r["articles_processed"] for r in results)
    successful_topics = sum(1 for r in results if r["status"] == "completed")
    
    print(f"Total topics processed: {len(results)}")
    print(f"Successful topics: {successful_topics}")
    print(f"Total articles created: {total_articles}")
    
    if successful_topics < len(results):
        print("\nTopics with errors:")
        for r in results:
            if r["status"] != "completed":
                print(f"- {r['topic']}: {r['error']}")
    
    return results

if __name__ == "__main__":
    # Allow custom limit from command line
    limit = 3
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Invalid limit: {sys.argv[1]}. Using default limit of 3.")
    
    run_scraper_for_all_default_topics(limit_per_topic=limit) 