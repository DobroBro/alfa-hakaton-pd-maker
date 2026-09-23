from pydantic import BaseModel, ConfigDict


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    payload: str
    payload_id: str


class ProcessResponse(BaseModel):
    result: str