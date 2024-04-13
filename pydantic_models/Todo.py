from pydantic import BaseModel

class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool = False

    class Config:
        orm_mode = True
