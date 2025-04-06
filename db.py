from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URI = os.getenv("MONGO")

mongo_client = MongoClient(MONGODB_URI)