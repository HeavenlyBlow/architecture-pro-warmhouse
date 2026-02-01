from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class CommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"


class CommandCreate(BaseModel):
    device_id: str = Field(..., description="ID устройства")
    action: str = Field(..., description="Действие для выполнения")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Параметры команды")


class Command(BaseModel):
    id: int
    command_id: str
    device_id: str
    action: str
    params: Optional[Dict[str, Any]]
    status: CommandStatus
    created_at: datetime
    executed_at: Optional[datetime]


class CommandResponse(BaseModel):
    command_id: str
    device_id: str
    action: str
    params: Optional[Dict[str, Any]]
    status: CommandStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
