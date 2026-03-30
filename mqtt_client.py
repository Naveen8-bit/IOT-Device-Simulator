import paho.mqtt.client as mqtt
import logging
import time

class MQTTClient:
    def __init__(self):

        self.broker = "broker.hivemq.com"
        self.port = 1883

        self.client = mqtt.Client()

        self.client.on_disconnect = self.on_disconnect

        self.client.connect(self.broker, self.port)

        self.client.loop_start()

    def on_disconnect(self, client, userdata, rc):
        logging.error("Disconnected from MQTT broker")

        while True:
            try:
                logging.info("Attempting to reconnect...")
                client.reconnect()
                logging.info("Reconnected successfully")
                break
            except Exception as e:
                logging.error(f"Reconnect failed: {e}")
                time.sleep(5)

    def publish(self, topic, message):
        self.client.publish(topic, message, qos=1)
        logging.info(f"Published to {topic}: {message}")
