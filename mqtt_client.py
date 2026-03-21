import paho.mqtt.client as mqtt
import logging

class MQTTClient:
    def __init__(self):

        self.broker = "broker.hivemq.com"
        self.port = 1883

        self.client = mqtt.Client()

        self.client.connect(self.broker, self.port)
        
    def publish(self, topic, message):

        self.client.publish(topic, message)

        logging.info(f"Published to {topic}: {message}")
