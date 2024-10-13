from fastapi import FastAPI, HTTPException, UploadFile, File as FastAPIFile, Form
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional
from datetime import datetime
import os
import shutil
from dotenv import load_dotenv
import uuid
import json

# Load environment variables
load_dotenv()

# MongoDB connection setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client['fastapi_app']
users_collection = db['users']
projects_collection = db['projects']
files_collection = db['files']

api_key = os.getenv("OPENAI_API_KEY")
weaviate_url = os.getenv("WEAVIATE_URL")

# FastAPI app
app = FastAPI()

# Custom JSON encoder to handle ObjectId and datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def custom_jsonable_encoder(obj):
    return json.loads(json.dumps(obj, cls=CustomJSONEncoder))

# Pydantic Models
class User(BaseModel):
    userID: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userName: str
    projectIDs: list = Field(default_factory=list)
    createdOn: datetime = Field(default_factory=datetime.utcnow)
    updatedOn: datetime = Field(default_factory=datetime.utcnow)

class Project(BaseModel):
    projectID: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userID: str
    projectName: str
    createdOn: datetime = Field(default_factory=datetime.utcnow)
    updatedOn: datetime = Field(default_factory=datetime.utcnow)

class FileModel(BaseModel):
    fileID: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fileName: str
    projectID: str
    userID: str
    createdOn: datetime = Field(default_factory=datetime.utcnow)
    updatedOn: datetime = Field(default_factory=datetime.utcnow)

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI MongoDB app"}

# User Routes
@app.post("/users/")
async def create_user(userName: str = Form(...)):
    user = User(userName=userName)
    users_collection.insert_one(user.dict())
    return {"userID": user.userID}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = users_collection.find_one({"userID": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return custom_jsonable_encoder(user)

@app.put("/users/{user_id}")
async def update_user(user_id: str, userName: Optional[str] = Form(None)):
    update_data = {
        "userName": userName,
        "updatedOn": datetime.utcnow()
    }
    update_data = {k: v for k, v in update_data.items() if v is not None}

    result = users_collection.update_one({"userID": user_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = users_collection.delete_one({"userID": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Project Routes
@app.post("/projects/")
async def create_project(userID: str = Form(...), projectName: str = Form(...)):
    project = Project(userID=userID, projectName=projectName)
    projects_collection.insert_one(project.dict())

    # Update the corresponding user's projectIDs list
    users_collection.update_one(
        {"userID": userID},
        {"$push": {"projectIDs": project.projectID}}
    )

    return {"projectID": project.projectID}

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = projects_collection.find_one({"projectID": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return custom_jsonable_encoder(project)

@app.put("/projects/{project_id}")
async def update_project(project_id: str, userID: Optional[str] = Form(None), projectName: Optional[str] = Form(None)):
    update_data = {
        "userID": userID,
        "projectName": projectName,
        "updatedOn": datetime.utcnow()
    }
    update_data = {k: v for k, v in update_data.items() if v is not None}

    result = projects_collection.update_one({"projectID": project_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated successfully"}

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    project = projects_collection.find_one({"projectID": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = projects_collection.delete_one({"projectID": project_id})
    if result.deleted_count > 0:
        # Remove the projectID from the user's projectIDs list
        users_collection.update_one(
            {"userID": project['userID']},
            {"$pull": {"projectIDs": project_id}}
        )
    else:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}

# File Routes
@app.post("/files/")
async def upload_file(file: UploadFile, userID: str = Form(...), projectID: str = Form(...)):
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_model = FileModel(fileName=file.filename, userID=userID, projectID=projectID)
    files_collection.insert_one(file_model.dict())
    return {"fileID": file_model.fileID}

@app.get("/files/{file_id}")
async def get_file(file_id: str):
    file = files_collection.find_one({"fileID": file_id})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return custom_jsonable_encoder(file)

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    result = files_collection.delete_one({"fileID": file_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted successfully"}
