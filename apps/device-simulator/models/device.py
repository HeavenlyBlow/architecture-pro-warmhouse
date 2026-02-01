from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    device_id: str = Field(..., description="ID устройства")
    device_type: str = Field(default="temperature_sensor", description="Тип устройства")
    name: str = Field(default="Simulated Device", description="Название устройства")


class SimulatedDevice(BaseModel):
    device_id: str
    device_type: str
    name: str
    is_active: bool = True
    is_paired: bool = False
    paired_user_id: Optional[str] = None
    last_telemetry: Optional[datetime] = None
    current_value: float = 20.0


class TelemetryData(BaseModel):
    device_id: str = Field(..., description="ID устройства")
    type: str = Field(default="temperature", description="Тип телеметрии")
    value: float = Field(..., description="Значение")
    unit: str = Field(default="celsius", description="Единица измерения")
