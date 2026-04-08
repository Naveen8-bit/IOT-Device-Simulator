import paho.mqtt.client as mqtt
import threading
from queue import Queue
import uuid
import json
from local_store import LocalStore

class MQTTClient:
    def __init__(self):
        print("[SYSTEM] Device starting...")

        self.broker = "broker.hivemq.com"
        self.port   = 1883

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect    = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.store = LocalStore()

        self.connected = False
        self.queue = Queue()

        # Counters
        self.total_generated = 0
        self.total_sent = 0
        self.total_stored = 0

        self.client.connect(self.broker, self.port)
        self.client.loop_start()

        threading.Thread(target=self._publisher_worker, daemon=True).start()

    def enqueue(self, topic, message):
        msg_id = str(uuid.uuid4())[:8]
        self.queue.put((msg_id, topic, message))
        self.total_generated += 1

    def _create_payload(self, msg_id, topic, message):
        parts = topic.split("/")
        sensor_id = parts[-2]
        data_type = parts[-1]

        return json.dumps({
            "id": msg_id,
            "sensor_id": sensor_id,
            "type": data_type,
            "value": message
        })

    def _publisher_worker(self):
        while True:
            msg_id, topic, message = self.queue.get()

            payload = self._create_payload(msg_id, topic, message)

            if self.connected:
                result = self.client.publish(topic, payload, qos=1)

                if result.rc == 0:
                    self.total_sent += 1

                    if self.total_sent % 50 == 0:
                        print(f"[PUBLISHED] Total sent: {self.total_sent}")
                else:
                    print("[ERROR] Publish failed → storing locally")
                    self.store.save(msg_id, topic, message)
                    self.total_stored += 1
            else:
                print("[OFFLINE] Storing data locally")
                self.store.save(msg_id, topic, message)
                self.total_stored += 1

            self.queue.task_done()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("[MQTT] Connected to broker")
        self.connected = True

        unsent = self.store.get_unsent()

        if unsent:
            print(f"[MQTT] Sending {len(unsent)} stored messages...")

            sent_ids = []

            for msg_id, topic, message in unsent:
                payload = self._create_payload(msg_id, topic, message)

                result = self.client.publish(topic, payload, qos=1)

                if result.rc == 0:
                    sent_ids.append(msg_id)
                    self.total_sent += 1
                else:
                    print(f"[ERROR] Failed to send stored message {msg_id}")

            # mark sent AFTER publishing loop
            for msg_id in sent_ids:
                self.store.mark_sent(msg_id)

            self.store.cleanup_sent()
            print("[MQTT] Stored messages sent and cleaned")

        self.print_stats()

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print("[MQTT] Disconnected")
        print("[MQTT] Data will now be store locally")
        self.connected = False

    def print_stats(self):
        print("\n========== STATS ==========")
        print(f"Generated : {self.total_generated}")
        print(f"Sent      : {self.total_sent}")
        print(f"Stored    : {self.total_stored}")
        print("===========================\n")
