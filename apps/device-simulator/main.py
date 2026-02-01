import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from routers import simulator
from services.mqtt_service import MqttService
from services.device_manager import DeviceManager

mqtt_service = MqttService()
device_manager = DeviceManager(mqtt_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mqtt_service.connect()
    asyncio.create_task(mqtt_service.subscribe_loop())
    asyncio.create_task(device_manager.telemetry_loop())
    yield
    await mqtt_service.disconnect()


app = FastAPI(
    title="Device Simulator API",
    description="API для симуляции IoT устройств",
    version="1.0.0",
    lifespan=lifespan
)

app.state.mqtt = mqtt_service
app.state.device_manager = device_manager

app.include_router(simulator.router, prefix="/api/v1/simulator", tags=["simulator"])


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "ok", "service": "device-simulator"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Device Simulator API",
        version="1.0.0",
        description="API для симуляции IoT устройств",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
