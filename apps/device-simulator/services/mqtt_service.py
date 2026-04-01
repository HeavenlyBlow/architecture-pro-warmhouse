import asyncio
import json
import os
from datetime import datetime
from typing import Callable, Optional, Dict, Any

import paho.mqtt.client as mqtt


class MqttService:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._on_device_paired_callback: Optional[Callable] = None
        self._on_command_callback: Optional[Callable] = None

    def set_device_paired_callback(self, callback: Callable):
        self._on_device_paired_callback = callback

    def set_command_callback(self, callback: Callable):
        self._on_command_callback = callback

    async def connect(self):
        self.client = mqtt.Client(client_id="device-simulator")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        try:
            self.client.connect(self.broker, self.port, 60)
            print(f"Connecting to MQTT broker at {self.broker}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
            client.subscribe("devices/paired")
            client.subscribe("devices/+/commands")
            print("Subscribed to devices/paired and devices/+/commands")
        else:
            print(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with code: {rc}")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"Received message on {topic}: {payload}")

            if topic == "devices/paired":
                if self._on_device_paired_callback:
                    self._on_device_paired_callback(payload)
            elif "/commands" in topic:
                if self._on_command_callback:
                    self._on_command_callback(payload)
        except Exception as e:
            print(f"Error processing message: {e}")

    async def subscribe_loop(self):
        while True:
            if self.client:
                self.client.loop(timeout=0.1)
            await asyncio.sleep(0.1)

    async def publish_telemetry(self, device_id: str, telemetry_type: str, value: float, unit: str):
        if not self.client or not self.connected:
            print("MQTT client not connected")
            return False

        topic = f"devices/{device_id}/telemetry"
        payload = {
            "device_id": device_id,
            "type": telemetry_type,
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        result = self.client.publish(topic, json.dumps(payload), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published telemetry to {topic}: {value} {unit}")
            return True
        else:
            print(f"Failed to publish telemetry: {result.rc}")
            return False

    def publish_command_ack(self, command_id: str, device_id: str, status: str = "executed"):
        if not self.client or not self.connected:
            print("MQTT client not connected")
            return False

        topic = "commands/ack"
        payload = {
            "command_id": command_id,
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        result = self.client.publish(topic, json.dumps(payload), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published command ack for {command_id}: {status}")
            return True
        else:
            print(f"Failed to publish command ack: {result.rc}")
            return False

    async def disconnect(self):
        if self.client:
            self.client.disconnect()
            print("Disconnected from MQTT broker")
