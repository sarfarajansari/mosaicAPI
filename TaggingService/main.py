import logging
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv

# Import project components using direct imports
from db_handler import DbHandler
from tagging_logic import TaggingLogic
from tag_schema import TagResult
from llm_client import LLMClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global instances (initialized during lifespan)
app_state: Dict[str, Any] = {}

def process_records_background(db: DbHandler, logic: TaggingLogic, records: list):
    """Background task to process and tag a list of records."""
    count_success = 0
    count_fail = 0
    count_no_content = 0
    logger.info(f"Background task started: Processing {len(records)} records.")
    for record in records:
        record_id = record.get('_id')
        content = record.get('content') # Adjust if your content field name is different
        
        if not record_id:
            logger.warning("Skipping record with missing _id.")
            count_fail += 1
            continue
            
        if not content or not isinstance(content, str) or not content.strip():
            logger.warning(f"Skipping record ID {record_id}: Missing or invalid content field.")
            # Optionally update the record to mark it as skipped/failed due to no content
            # db.update_record_tags(record_id, ["_TAGGING_FAILED_NO_CONTENT"]) 
            count_no_content += 1
            continue

        try:
            # Get tags from LLM
            tag_result: TagResult = logic.get_tags_for_content(content)
            
            # Update record in DB
            success = db.update_record_tags(record_id, tag_result.tags)
            if success:
                logger.debug(f"Successfully tagged record ID {record_id} with tags: {tag_result.tags}")
                count_success += 1
            else:
                logger.warning(f"Failed to update tags for record ID {record_id}.")
                count_fail += 1
                
        except Exception as e:
            logger.error(f"Error processing record ID {record_id}: {e}", exc_info=True)
            count_fail += 1
            # Optionally mark the record as failed in the DB
            # db.update_record_tags(record_id, ["_TAGGING_FAILED_ERROR"])

    logger.info(f"Background task finished. Success: {count_success}, Failed: {count_fail}, No Content: {count_no_content}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info("Application startup...")
    try:
        db = DbHandler()
        logic = TaggingLogic() 
        app_state["db_handler"] = db
        app_state["tagging_logic"] = logic
        logger.info("Database handler and tagging logic initialized.")
    except Exception as e:
        logger.critical(f"Fatal error during application startup: {e}", exc_info=True)
        # Prevent application from starting if core components fail
        raise RuntimeError(f"Failed to initialize application components: {e}") from e
        
    yield # Application runs here
    
    logger.info("Application shutdown...")
    if "db_handler" in app_state:
        app_state["db_handler"].close_connection()
    logger.info("Resources cleaned up.")

app = FastAPI(
    lifespan=lifespan,
    title="AI Content Tagging Service",
    description="Provides endpoints to tag AI-related content stored in MongoDB."
)

@app.post("/process-unprocessed", status_code=status.HTTP_202_ACCEPTED)
async def trigger_processing(background_tasks: BackgroundTasks):
    """
    Triggers a background task to fetch and tag unprocessed records 
    (where 'assigned_tags' field doesn't exist).
    """
    logger.info("Received request to process unprocessed records.")
    db: DbHandler = app_state.get("db_handler")
    logic: TaggingLogic = app_state.get("tagging_logic")

    if not db or not logic:
        logger.error("Application components (DB/Logic) not initialized.")
        raise HTTPException(status_code=503, detail="Service components not ready.")

    if not db.is_connected():
        logger.error("Database connection is not active.")
        raise HTTPException(status_code=503, detail="Database connection unavailable.")

    try:
        # Fetch records within the request cycle to get an immediate count
        records_to_process = db.get_unprocessed_records(limit=5000) # Process up to 5000 records per trigger
        num_records = len(records_to_process)
        
        if num_records == 0:
            logger.info("No unprocessed records found to process.")
            return {"status": "success", "message": "No unprocessed records found.", "records_queued": 0}
        
        # Add the processing job to background tasks
        background_tasks.add_task(process_records_background, db, logic, records_to_process)
        
        logger.info(f"Queued {num_records} records for background tagging.")
        return {
            "status": "accepted", 
            "message": f"Background task started to process {num_records} records.",
            "records_queued": num_records
        }

    except Exception as e:
        logger.error(f"Error triggering processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger processing: {str(e)}")

# Optional: Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    db: DbHandler = app_state.get("db_handler")
    logic: TaggingLogic = app_state.get("tagging_logic")
    db_status = "connected" if db and db.is_connected() else "disconnected"
    logic_status = "initialized" if logic else "not initialized"
    
    status_code = status.HTTP_200_OK
    if db_status != "connected" or logic_status != "initialized":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {"status": "ok" if status_code == status.HTTP_200_OK else "error", 
            "database": db_status, 
            "tagging_logic": logic_status}

if __name__ == "__main__":
    import uvicorn
    # It's recommended to run using: uvicorn TaggingService.main:app --reload --host 0.0.0.0 --port 8001
    # The port 8001 is just an example, choose an available one.
    print("Starting Uvicorn server...")
    print("Run with: uvicorn TaggingService.main:app --reload --host 0.0.0.0 --port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)