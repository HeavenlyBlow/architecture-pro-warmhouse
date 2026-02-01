import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from routers import commands
from services.mqtt_service import MqttService
from services.database import Database
from models.command import CommandStatus

db = Database()
mqtt_service = MqttService()


def on_command_ack(payload: dict):
    command_id = payload.get("command_id")
    status = payload.get("status", "executed")
    
    if command_id:
        print(f"Received ack for command {command_id}: {status}")
        asyncio.create_task(handle_command_ack(command_id, status))


async def handle_command_ack(command_id: str, status: str):
    try:
        if status == "executed":
            await db.update_command_status(
                command_id,
                CommandStatus.EXECUTED,
                datetime.utcnow()
            )
            print(f"Command {command_id} marked as executed")
        elif status == "failed":
            await db.update_command_status(
                command_id,
                CommandStatus.FAILED,
                datetime.utcnow()
            )
            print(f"Command {command_id} marked as failed")
    except Exception as e:
        print(f"Error updating command status: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await mqtt_service.connect()
    mqtt_service.set_command_ack_callback(on_command_ack)
    asyncio.create_task(mqtt_service.subscribe_loop())
    yield
    await mqtt_service.disconnect()
    await db.disconnect()


app = FastAPI(
    title="Command Service API",
    description="API для управления командами устройств",
    version="1.0.0",
    lifespan=lifespan
)

app.state.db = db
app.state.mqtt = mqtt_service

app.include_router(commands.router, prefix="/api/v1/commands", tags=["commands"])


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "ok", "service": "command-service"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Command Service API",
        version="1.0.0",
        description="API для управления командами устройств",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
