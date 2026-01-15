from pydantic import BaseModel

class ProcessRequest(BaseModel):
    knowledge_base_id: str

