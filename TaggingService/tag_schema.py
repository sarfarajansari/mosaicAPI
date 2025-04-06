from pydantic import BaseModel, Field
from typing import List, Optional
import json

# --- Models for LLM Output ---

class TagResult(BaseModel):
    """Schema for the structured output from the tagging LLM."""
    tags: List[str] = Field(description="List of relevant tag names assigned to the content.")

# --- Models for loading Tags.json ---

class Tag(BaseModel):
    name: str
    description: Optional[str] = None

class TagCategory(BaseModel):
    category: str
    description: Optional[str] = None
    tags: List[Tag]

class TagConfig(BaseModel):
    namespace: str
    custom_tags: List[TagCategory]

# --- Helper Function ---
def load_tag_config(filepath: str = "Tags.json") -> TagConfig:
    """Loads the tag configuration from the JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return TagConfig(**data)
    except FileNotFoundError:
        print(f"Error: Tags file not found at {filepath}")
        raise
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while loading {filepath}: {e}")
        raise

def get_available_tags_string(tag_config: TagConfig) -> str:
    """Formats the available tags into a string suitable for the LLM prompt."""
    output_lines = []
    for category in tag_config.custom_tags:
        output_lines.append(f"\nCategory: {category.category} ({category.description or 'No description'})")
        for tag in category.tags:
            output_lines.append(f"  - {tag.name}: {tag.description or 'No description'}")
    return "\n".join(output_lines)

if __name__ == "__main__":
    # Example of loading and formatting
    try:
        config = load_tag_config()
        print("Tag Config Loaded Successfully:")
        # print(config.model_dump_json(indent=2))
        print("\nFormatted Available Tags for Prompt:")
        print(get_available_tags_string(config))
        
        print("\nTagResult Schema JSON:")
        print(TagResult.model_json_schema(indent=2))

    except Exception as e:
        print(f"Failed to load or process Tags.json: {e}") 