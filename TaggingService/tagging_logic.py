import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

# Change relative import to absolute
import config
from .tag_schema import TagResult, TagConfig, load_tag_config, get_available_tags_string

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TaggingLogic:
    """Handles the logic for generating tags using an LLM."""

    def __init__(self):
        try:
            # Load tag configuration once during initialization
            self.tag_config: TagConfig = load_tag_config()
            self.available_tags_str: str = get_available_tags_string(self.tag_config)
            
            # Initialize the LLM
            self.llm: AzureChatOpenAI = config.get_tagging_llm()
            
            # Define the prompt template
            self.prompt_template = self._create_prompt_template()
            
            # Create the tagging chain
            self.tagging_chain = self.prompt_template | self.llm.with_structured_output(
                TagResult, include_raw=False
            )
            logger.info("TaggingLogic initialized successfully.")

        except ValueError as ve:
            logger.error(f"Configuration error during TaggingLogic initialization: {ve}")
            raise
        except FileNotFoundError:
            logger.error("Tags.json file not found. Please ensure it exists in the TaggingService directory.")
            raise
        except Exception as e:
            logger.error(f"Error initializing TaggingLogic: {e}", exc_info=True)
            raise

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Creates the chat prompt template for the tagging task."""
        system_prompt = f"""
You are an expert tagging system for AI-related content scraped from the web (like research papers, blog posts, code repositories). Your sole responsibility is to analyze the provided text content and output a valid JSON object that strictly conforms to the following schema: 

```json
{{TagResult.model_json_schema(indent=2)}}
```

Available Tags (categorized): 
{self.available_tags_str}

Instructions:
1. Analyze the input text content carefully.
2. Assign tags from the 'Available Tags' list that are most relevant to the content.
3. Focus on accurately categorizing the content based on its subject matter, type, source, technical level, and potential applications.
4. Only assign tags that are clearly supported by the text.
5. Return the assigned tag names as a list of strings under the key "tags".
6. If no tags from the list clearly apply, return an empty list: {{"tags": []}}.
7. Do NOT include any tags that are not in the 'Available Tags' list.
8. Output ONLY the JSON object, with no introductory text, explanations, or apologies.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Please analyze and tag the following content:\n\n---\nContent Start:\n{input_content}\nContent End\n---"),
        ])

    def get_tags_for_content(self, content: str) -> TagResult:
        """Generates tags for the given content using the LLM chain."""
        if not content:
            logger.warning("Received empty content for tagging, returning no tags.")
            return TagResult(tags=[])
            
        # Truncate content if it's excessively long to avoid exceeding token limits
        # Adjust the limit based on model/API constraints
        max_content_length = 15000 # Example limit (approx 4k tokens)
        if len(content) > max_content_length:
            logger.warning(f"Content length ({len(content)}) exceeds limit ({max_content_length}). Truncating.")
            content = content[:max_content_length]
            
        try:
            logger.debug(f"Invoking tagging chain for content (first 100 chars): {content[:100]}...")
            result = self.tagging_chain.invoke({"input_content": content})
            logger.info(f"Successfully generated tags: {result.tags}")
            return result
        except Exception as e:
            logger.error(f"Error invoking tagging chain: {e}", exc_info=True)
            # Return empty tags on error to avoid breaking the process
            return TagResult(tags=[]) 

if __name__ == "__main__":
    try:
        tagging_logic = TaggingLogic()
        print("TaggingLogic initialized.")

        # --- Example Usage ---
        example_content_1 = """
        Researchers at Stanford University have released a new paper on ArXiv detailing a novel approach 
        to Reinforcement Learning using Mixture of Experts (MoE) models. The accompanying code is available 
        on GitHub under the MIT License. This advanced technique shows promise for complex robotic control tasks.
        """
        
        example_content_2 = """
        Check out this cool new app I built for ordering pizza! #food #app #coding
        """
        
        example_content_3 = """        
        Llama 3, the latest large language model from Meta AI, has been released. This transformer-based model 
        builds upon previous versions, offering improved performance in text generation and summarization tasks. 
        It's available for researchers and developers.
        """

        print("\nTesting with Example Content 1 (AI Research):")
        tags_result_1 = tagging_logic.get_tags_for_content(example_content_1)
        print(f"Assigned Tags: {tags_result_1.tags}")

        print("\nTesting with Example Content 2 (Irrelevant):")
        tags_result_2 = tagging_logic.get_tags_for_content(example_content_2)
        print(f"Assigned Tags: {tags_result_2.tags}")
        
        print("\nTesting with Example Content 3 (LLM Release):")
        tags_result_3 = tagging_logic.get_tags_for_content(example_content_3)
        print(f"Assigned Tags: {tags_result_3.tags}")

    except Exception as e:
        print(f"An error occurred during TaggingLogic test: {e}") 