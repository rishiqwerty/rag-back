from sqlalchemy import Column, String, DateTime, Integer
from .database import Base
import datetime


class TaskStatus(Base):
    __tablename__ = "task_status"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(String)
    file_name = Column(String)
    file_path = Column(String)
    user_email = Column(String)
    error_message = Column(String, nullable=True)
    additional_info = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    completed_at = Column(DateTime, nullable=True)
