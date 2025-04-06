import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Import config (assuming it's in the same directory)
import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DbHandler:
    """Handles interactions with the MongoDB database."""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection."""
        if not config.MONGODB_SRC_URI:
            logger.error("MongoDB connection string (MONGODB_SRC_URI) not set.")
            raise ValueError("MongoDB connection string not configured.")
        try:
            self.client = MongoClient(
                config.MONGODB_SRC_URI,
                serverSelectionTimeoutMS=5000 # Timeout after 5 seconds
            )
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB.")
            self.db = self.client[config.MONGODB_MOSIAC_DATABASE]
            
            # Use the MONGODB_DATA_COLLECTION for tagging operations
            if not config.MONGODB_DATA_COLLECTION:
                 logger.error("Target MongoDB collection (MONGODB_DATA_COLLECTION) not set in environment.")
                 raise ValueError("Target MongoDB collection not configured.")
                 
            self.collection = self.db[config.MONGODB_DATA_COLLECTION] 
            logger.info(f"Using database '{config.MONGODB_MOSIAC_DATABASE}' and target collection '{config.MONGODB_DATA_COLLECTION}' for tagging.")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            raise

    def is_connected(self) -> bool:
        """Check if the MongoDB client is connected."""
        return self.client is not None

    def get_unprocessed_records(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetches records that have not yet been tagged.

        Assumes untagged records are those where the 'assigned_tags' field does not exist.
        Includes the 'content' field needed for tagging.
        """
        if not self.is_connected() or self.collection is None:
            logger.error("Not connected to MongoDB.")
            return []
        
        try:
            # Find documents where 'assigned_tags' does not exist
            # Only retrieve _id and the content field needed for tagging
            cursor = self.collection.find(
                {"assigned_tags": {"$exists": False}},
                {"_id": 1, "content": 1} # Adjust "content" if the field name is different
            ).limit(limit)
            
            records = list(cursor)
            logger.info(f"Fetched {len(records)} unprocessed records (limit: {limit}).")
            return records
        except OperationFailure as e:
            logger.error(f"Error fetching unprocessed records: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching records: {e}")
            return []

    def update_record_tags(self, record_id: Any, tags: List[str]) -> bool:
        """Updates a record with the assigned tags and a timestamp.
        
        Args:
            record_id: The ObjectId of the record to update.
            tags: A list of strings representing the assigned tags.

        Returns:
            True if the update was successful, False otherwise.
        """
        if not self.is_connected() or self.collection is None:
            logger.error("Not connected to MongoDB.")
            return False

        try:
            result = self.collection.update_one(
                {"_id": record_id},
                {
                    "$set": {
                        "assigned_tags": tags,
                        "tags_assigned_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 1:
                # logger.debug(f"Successfully assigned tags {tags} to record ID {record_id}") # Debug level might be better
                return True
            elif result.matched_count == 1 and result.modified_count == 0:
                logger.warning(f"Record ID {record_id} matched but was not modified (perhaps tags were already set?).")
                return False # Or True depending on desired behavior if already tagged
            else:
                logger.warning(f"Record ID {record_id} not found for updating tags.")
                return False
        except OperationFailure as e:
            logger.error(f"Error updating record {record_id} with tags: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred updating record {record_id}: {e}")
            return False

    def close_connection(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")
            self.client = None

if __name__ == "__main__":
    try:
        db_handler = DbHandler()
        if db_handler.is_connected():
            print("Fetching a few unprocessed records...")
            records = db_handler.get_unprocessed_records(limit=5)
            if records:
                print(f"Found {len(records)} records:")
                for record in records:
                    print(f"  ID: {record['_id']}, Has Content: {'content' in record}")
                    # Example update (use with caution on real data)
                    # success = db_handler.update_record_tags(record['_id'], ["test_tag", "example"])
                    # print(f"  Update successful: {success}")
            else:
                print("No unprocessed records found (or DB error).")
            db_handler.close_connection()
        else:
            print("Could not establish DB connection.")
    except Exception as e:
        print(f"An error occurred during DB handler test: {e}")