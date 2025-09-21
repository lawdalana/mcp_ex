from fastapi import FastAPI
from app.schema import RequestConversation


app = FastAPI()

@app.get("/")
async def hello_world():
    return {"Hello": "World"}

@app.post("/conversation")
async def conversation(request: RequestConversation):
    return {"message": "This is the conversation endpoint", "data": request}