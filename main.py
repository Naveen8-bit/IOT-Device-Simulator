import time
import json
import yaml
from datetime import datetime

from sensor import TemperatureSensor
from mqtt_client import MQTTClient
from logger import setup_logger

logging = setup_logger()

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

device_id = config["device_id"]
topic = config["mqtt_topic"]
interval = config["interval"]

sensor = TemperatureSensor()
mqtt = MQTTClient()

logging.info("Device Started")

while True:

    try:

        temp = sensor.read_temperature()

        data = {
            "device_id": device_id,
            "temperature": temp,
            "status": "OK"
        }

        message = json.dumps(data)

        mqtt.publish(topic, message)

    except Exception as e:

        error_data = {
            "device_id": device_id,
            "status": "ERROR",
            "message": str(e)
        }

        mqtt.publish(topic, json.dumps(error_data))

    time.sleep(interval)
