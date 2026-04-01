from typing import List

from fastapi import APIRouter, HTTPException, Request

from models.device import SimulatedDevice, DeviceCreate, TelemetryData

router = APIRouter()


@router.get(
    "/devices",
    response_model=List[SimulatedDevice],
    summary="Get simulated devices",
    description="Получить список всех симулируемых устройств"
)
async def get_devices(request: Request):
    device_manager = request.app.state.device_manager
    return device_manager.get_devices()


@router.get(
    "/devices/available",
    response_model=List[SimulatedDevice],
    summary="Get available devices",
    description="Получить список устройств, доступных для привязки"
)
async def get_available_devices(request: Request):
    device_manager = request.app.state.device_manager
    return device_manager.get_available_devices()


@router.get(
    "/devices/{device_id}/available",
    summary="Check if device is available",
    description="Проверить доступно ли устройство для привязки"
)
async def check_device_available(request: Request, device_id: str):
    device_manager = request.app.state.device_manager
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in simulator")
    return {
        "device_id": device_id,
        "available": not device.is_paired,
        "is_paired": device.is_paired,
        "paired_user_id": device.paired_user_id
    }


@router.post(
    "/devices",
    response_model=SimulatedDevice,
    status_code=201,
    summary="Add simulated device",
    description="Добавить новое устройство в симулятор"
)
async def add_device(request: Request, device: DeviceCreate):
    device_manager = request.app.state.device_manager
    return device_manager.add_device(device)


@router.delete(
    "/devices/{device_id}",
    summary="Remove simulated device",
    description="Удалить устройство из симулятора"
)
async def remove_device(request: Request, device_id: str):
    device_manager = request.app.state.device_manager
    if device_manager.remove_device(device_id):
        return {"message": f"Device {device_id} removed"}
    raise HTTPException(status_code=404, detail="Device not found")


@router.post(
    "/devices/{device_id}/telemetry",
    summary="Send telemetry manually",
    description="Отправить телеметрию от устройства вручную"
)
async def send_telemetry(request: Request, device_id: str, telemetry: TelemetryData):
    device_manager = request.app.state.device_manager
    
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in simulator")

    success = await device_manager.send_telemetry(
        device_id=device_id,
        telemetry_type=telemetry.type,
        value=telemetry.value,
        unit=telemetry.unit
    )
    
    if success:
        return {"message": "Telemetry sent", "device_id": device_id, "value": telemetry.value}
    raise HTTPException(status_code=500, detail="Failed to send telemetry")
