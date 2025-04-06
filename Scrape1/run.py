"""
AI Article Generator - Main Interface

This script provides a simple interface for generating AI articles
either individually or in batch.
"""
import sys
import argparse
import subprocess
import os

def check_environment():
    """Check if all required environment variables are set."""
    from config import TAVILY_API_KEY, MONGODB_SRC_URI, AZURE_OPENAI_API_KEY
    
    issues = []
    
    if not TAVILY_API_KEY:
        issues.append("TAVILY_API_KEY is not set")
    
    if not MONGODB_SRC_URI:
        issues.append("MONGODB_SRC_URI is not set")
    
    if not AZURE_OPENAI_API_KEY:
        issues.append("AZURE_OPENAI_API_KEY is not set")
    
    return issues

def main():
    """Main entry point for the AI article generator interface."""
    parser = argparse.ArgumentParser(description="AI Article Generator")
    parser.add_argument("--batch", action="store_true", 
                        help="Run in batch mode to generate multiple articles")
    parser.add_argument("--articles", type=int, default=5,
                        help="Number of articles to generate in batch mode (default: 5)")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay in seconds between articles in batch mode (default: 5)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file for batch results")
    parser.add_argument("--topic", type=str, default=None,
                        help="Specific topic for single article generation")
    parser.add_argument("--topics-file", type=str, default=None,
                        help="JSON file containing list of topics to process in batch mode")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check environment setup without generating articles")
    
    args = parser.parse_args()
    
    # Print welcome message
    print("\n==== AI Article Generator ====")
    
    # Check environment if dry run
    if args.dry_run:
        print("Checking environment setup...")
        issues = check_environment()
        
        if issues:
            print("\n⚠️ Environment issues found:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nPlease check your .env file and ensure all required variables are set.")
            return 1
        else:
            print("\n✅ Environment setup looks good! All required variables are set.")
            print("\nYou can now run the generator without the --dry-run flag.")
            return 0
    
    if args.batch:
        print("Running in batch mode")
        print(f"Number of articles: {args.articles}")
        print(f"Delay between articles: {args.delay} seconds")
        if args.output:
            print(f"Output file: {args.output}")
        if args.topics_file:
            print(f"Topics file: {args.topics_file}")
        print("============================\n")
        
        # Construct command for batch article generator
        cmd = [sys.executable, "batch_article_generator.py"]
        cmd.extend(["--articles", str(args.articles)])
        cmd.extend(["--delay", str(args.delay)])
        if args.output:
            cmd.extend(["--output", args.output])
        if args.topics_file:
            cmd.extend(["--topics-file", args.topics_file])
        
        # Run batch generator
        return subprocess.call(cmd)
    else:
        print("Running in single article mode")
        if args.topic:
            print(f"Topic: {args.topic}")
        print("============================\n")
        
        # For single article, we need to create a custom script that accepts a topic
        # Since article_generator.py doesn't currently accept command line args
        # we'll use a different approach
        
        # Import function directly
        from article_generator import generate_and_store_article
        
        # Generate and store the article
        result = generate_and_store_article(args.topic)
        
        # Print results
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
    sys.exit(main()) 