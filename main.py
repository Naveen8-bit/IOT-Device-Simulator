import threading
import time
import random
import yaml

from sensor import Sensor
from mqtt_client import MQTTClient
from logger import setup_logger

logging = setup_logger()

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

DEVICE_PREFIX = config["device_prefix"]
BASE_TOPIC    = config["mqtt_base_topic"]
INTERVAL_MIN  = config["interval_min"]
INTERVAL_MAX  = config["interval_max"]
NUM_SENSORS   = config["num_sensors"]

# init mqtt (starts connection and publisher thread)
mqtt = MQTTClient()


def sensor_worker(sensor_id):
    sensor = Sensor()

    while True:
        base_topic = f"{BASE_TOPIC}/{DEVICE_PREFIX}_{sensor_id}"

        try:
            temp     = sensor.read_temperature()
            humidity = sensor.read_humidity()
            status   = sensor.get_status()

            # push to queue (publisher thread handles sending)
            mqtt.enqueue(f"{base_topic}/temperature", temp)
            mqtt.enqueue(f"{base_topic}/humidity", humidity)
            mqtt.enqueue(f"{base_topic}/status", status)

            if sensor_id % 25 == 0:
                logging.info(f"{base_topic} data sent")

        except Exception as e:
            mqtt.enqueue(f"{base_topic}/status", f"ERROR: {str(e)}")
            logging.error(f"{base_topic} error")

        time.sleep(random.uniform(INTERVAL_MIN, INTERVAL_MAX))


threads = []

for i in range(1, NUM_SENSORS + 1):
    t = threading.Thread(target=sensor_worker, args=(i,))
    t.daemon = True
    t.start()
    threads.append(t)

for t in threads:
    t.join()


        mqtt.publish(topic, json.dumps(error_data))

    time.sleep(interval)
