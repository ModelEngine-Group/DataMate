from pydantic import BaseModel

class ProcessRequest(BaseModel):
    knowledge_base_id: str

class QueryRequest(BaseModel):
    knowledge_base_id: str
    query: str
