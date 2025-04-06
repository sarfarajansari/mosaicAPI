
from google import genai
from qdrant_client import QdrantClient

from bson.objectid import ObjectId
from db import mongo_client

from dotenv import load_dotenv
import os
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI")
QDRANT_API_KEY = os.getenv("QDRANT")
# --- Initialize Gemini ---
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# --- Initialize Qdrant ---
qdrant_client = QdrantClient(
    url="https://0000a9bd-416c-4682-a878-063659ba2c93.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key=QDRANT_API_KEY
)

# --- Initialize MongoDB ---

db = mongo_client["mosaic"]
collection = db["data2"]

# --- Master function ---
def get_documents_from_query(user_query: str,n:int=10):
    # Step 1: Get embedding from Gemini
    result = genai_client.models.embed_content(
        model="text-embedding-004",
        contents=user_query
    )
    query_vector = result.embeddings[0].values

    # Step 2: Search in Qdrant for top 10 similar vectors
    hits = qdrant_client.search(
        collection_name="data",
        query_vector=query_vector,
        limit=n
    )

    # Step 3: Extract MongoDB IDs from Qdrant payloads
    object_ids = []
    for hit in hits:
        try:
            _id = hit.payload["_id"]
            object_ids.append(ObjectId(_id))
        except Exception as e:
            print(f"Skipping invalid ID: {hit.payload.get('_id')} -> {e}")

    # Step 4: Query MongoDB
    documents = collection.find({"_id": {"$in": object_ids}}).to_list()

    for t in documents:
        t['id'] = str(t['_id'])
        del t['_id']
    return list(documents)

