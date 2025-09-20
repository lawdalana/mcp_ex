from pydantic import BaseModel

class RequestConversation(BaseModel):
    question: str
    interaction_id: str