from pydantic import BaseModel, EmailStr

class TaskStatusCreate(BaseModel):
    file_name: str
    user_email: EmailStr
