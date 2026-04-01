import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional

from models.device import SimulatedDevice, DeviceCreate


class DeviceManager:
    def __init__(self, mqtt_service):
        self.mqtt_service = mqtt_service
        self.devices: Dict[str, SimulatedDevice] = {}
        self._telemetry_interval = 30

        mqtt_service.set_device_paired_callback(self._on_device_paired)
        mqtt_service.set_command_callback(self._on_command)

    def _on_device_paired(self, payload: dict):
        device_id = payload.get("device_id")
        user_id = payload.get("user_id")

        if device_id and device_id in self.devices:
            device = self.devices[device_id]
            device.is_paired = True
            device.paired_user_id = user_id
            print(f"Device {device_id} paired with user {user_id}")

    def _on_command(self, payload: dict):
        command_id = payload.get("command_id")
        device_id = payload.get("device_id")
        action = payload.get("action")
        params = payload.get("params", {})

        print(f"Received command {command_id} for device {device_id}: {action} with params {params}")

        if device_id in self.devices:
            device = self.devices[device_id]
            executed = False
            
            if action == "set_temperature" and "target" in params:
                device.current_value = float(params["target"])
                print(f"Device {device_id} temperature set to {device.current_value}")
                executed = True
            elif action == "toggle":
                device.is_active = not device.is_active
                print(f"Device {device_id} toggled to {device.is_active}")
                executed = True
            
            if executed and command_id:
                self.mqtt_service.publish_command_ack(command_id, device_id, "executed")
        else:
            if command_id:
                self.mqtt_service.publish_command_ack(command_id, device_id, "failed")

    def add_device(self, device_create: DeviceCreate) -> SimulatedDevice:
        device = SimulatedDevice(
            device_id=device_create.device_id,
            device_type=device_create.device_type,
            name=device_create.name,
            is_active=True,
            current_value=20.0 + random.uniform(-5, 5)
        )
        self.devices[device.device_id] = device
        return device

    def remove_device(self, device_id: str) -> bool:
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False

    def get_devices(self) -> List[SimulatedDevice]:
        return list(self.devices.values())

    def get_available_devices(self) -> List[SimulatedDevice]:
        return [d for d in self.devices.values() if not d.is_paired]

    def get_device(self, device_id: str) -> Optional[SimulatedDevice]:
        return self.devices.get(device_id)

    def is_device_available(self, device_id: str) -> bool:
        device = self.devices.get(device_id)
        return device is not None and not device.is_paired

    async def send_telemetry(self, device_id: str, telemetry_type: str, value: float, unit: str):
        device = self.devices.get(device_id)
        if not device:
            return False

        await self.mqtt_service.publish_telemetry(device_id, telemetry_type, value, unit)
        device.last_telemetry = datetime.utcnow()
        device.current_value = value
        return True

    async def telemetry_loop(self):
        while True:
            for device_id, device in self.devices.items():
                if device.is_active:
                    value = device.current_value + random.uniform(-0.5, 0.5)
                    device.current_value = value

                    telemetry_type = "temperature"
                    unit = "celsius"
                    if device.device_type == "humidity_sensor":
                        telemetry_type = "humidity"
                        unit = "percent"

                    await self.mqtt_service.publish_telemetry(
                        device_id,
                        telemetry_type,
                        round(value, 2),
                        unit
                    )
                    device.last_telemetry = datetime.utcnow()

            await asyncio.sleep(self._telemetry_interval)
