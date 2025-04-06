"""
Main entry point for the AI topic scraper workflow.
This script provides a command-line interface for running the AI scraper.
"""
import sys
import argparse
from ai_scraper_workflow import run_ai_scraper

def main():
    """Main entry point for the AI scraper."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="AI Topic Scraper")
    parser.add_argument("topic", help="AI topic to search for (e.g., 'large language models')")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of articles to process")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print welcome message
    print(f"\n==== AI Topic Scraper ====")
    print(f"Topic: {args.topic}")
    print(f"Article limit: {args.limit}")
    print("=========================\n")
    
    # Run the scraper with limit parameter
    result = run_ai_scraper(args.topic, limit=args.limit)
    
    # Print results
    print("\n==== Scraping Results ====")
    print(f"Status: {result['status']}")
    print(f"Articles processed: {result.get('articles_processed', 0)}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    print(f"Trace ID: {result['trace_id']}")
    print("=========================\n")
    
    # Return appropriate exit code
    if result['status'] == 'completed':
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 