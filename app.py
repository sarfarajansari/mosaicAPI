from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from db import mongo_client
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
from bson import ObjectId
from search import get_documents_from_query
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/single")
def get_single_listing(id: str):
    doc = mongo_client["mosaic"]["data2"].find_one({"_id": ObjectId(id)})
    if not doc:
        return {"error": "Document not found"}
    
    # Convert ObjectId to string for JSON serialization
    doc["_id"] = str(doc["_id"])
    
    # Remove the "coords" field if it exists
    if "coords" in doc:
        del doc["coords"]
    
    return doc

@app.get("/listings")
def get_listings(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=500),type:str=Query(None)):
    
    skip = (page - 1) * page_size
    query = {}
    if type and type!="All":
        query["type"] = type
    data = mongo_client["mosaic"]["data2"].aggregate([
        {"$match": query},  # Match all documents
        {"$skip": skip},
        {"$limit": page_size},
        # {"$project": {"_id": 0}}  # Exclude the _id field
    ]).to_list()

    for i in data:
        # print(str(i['_id']))
        i['id'] = str(i['_id'])
        del i['_id']

    total_count = mongo_client["mosaic"]["data2"].count_documents(query)
    total_pages = (total_count + page_size - 1) // page_size
    return {
        "page": page,
        "page_size": page_size,
        "data": list(data),
        "total_count": total_count,
        "total_pages": total_pages,
    }


@app.get("/getsimilar",)
def get_similar(id:str):
    doc = mongo_client["mosaic"]["data2"].find_one({"_id":ObjectId(id) })

    if not doc:
        return {"error": "Document not found"}
    
    q= ''

    if doc['type'] == 'AI Tool':
        q = f"{doc['metadata']['title']} {doc['content']['description']}"

    if doc['type'] == 'Model':
        q = f"{doc['Model']} {doc['Abstract']}"

    if doc['type'] == 'Article':
        q = f"{doc['metadata']['title']} {doc['content']['description']}"

    return get_documents_from_query(q, n=6)

    
    

@app.get("/search")
def get_search_results(query:str):
    return get_documents_from_query(query, n=12)







@app.get("/initialize-discover")
def initialise_discover():
    
    data =mongo_client['mosaic']['data2'].aggregate([
        {
            '$match':{
                "coords":{
                    "$exists": True,
                    "$ne": None
                }
            }
        },
        {
            '$limit':200
        },
        {
            "$project": {
                "_id":1,
                "coords": 1,
                "type": 1,
                "name": "$metadata.title",
                "model": "$Model",
            }
        }
    ]).to_list()

    for i in data:
        # print(str(i['_id']))
        i['id'] = str(i['_id'])
        i['_id'] = str(i['_id'])


    return data



