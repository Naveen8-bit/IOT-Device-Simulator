import paho.mqtt.client as mqtt
import threading
from queue import Queue
import uuid
import json
import time
from local_store import LocalStore


class MQTTClient:
    def __init__(self):
        print("[SYSTEM] Device starting...")

        self.broker = "broker.hivemq.com"
        self.port = 1883

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        # Auto reconnect
        self.client.reconnect_delay_set(min_delay=1, max_delay=5)

        # Limit in-flight messages
        self.client.max_inflight_messages_set(50)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.store = LocalStore()

        self.connected = False
        self.recovering = False

        # logging helpers
        self.offline_counter = 0
        self.was_offline = False

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
        return json.dumps({
            "id": msg_id,
            "sensor_id": parts[-2],
            "type": parts[-1],
            "value": message
        })

    def _publisher_worker(self):
        while True:
            msg_id, topic, message = self.queue.get()

            # Wait during recovery (no requeue)
            if self.recovering:
                time.sleep(0.05)
                self.queue.task_done()
                continue

            payload = self._create_payload(msg_id, topic, message)

            if self.connected and self.client.is_connected():

                result = self.client.publish(topic, payload, qos=1)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.total_sent += 1

                    if self.total_sent % 200 == 0:
                        print(f"[LIVE] Messages sent: {self.total_sent}")

                else:
                    print("[ERROR] Publish failed → saving locally")
                    self.store.save(msg_id, topic, message)
                    self.total_stored += 1

                time.sleep(0.002)

            else:
                #OFFLINE LOGGING
                self.offline_counter += 1
                self.was_offline = True

                if self.offline_counter % 100 == 0:
                    print(f"[OFFLINE] Stored {self.offline_counter} messages locally")

                self.store.save(msg_id, topic, message)
                self.total_stored += 1

            self.queue.task_done()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("\n[MQTT] Connected to broker")

        if reason_code != 0:
            print("[MQTT] Connection failed")
            self.connected = False
            return

        self.connected = True

        #Show reconnect message only once
        if self.was_offline:
            print("[SYSTEM] Connection restored. Starting recovery...\n")
            self.was_offline = False
            self.offline_counter = 0

        threading.Thread(target=self._recover_messages, daemon=True).start()

    def _recover_messages(self):
        unsent = self.store.get_unsent()

        if not unsent:
            print("[MQTT] No stored messages. Normal operation resumed.")
            return

        self.recovering = True

        total = len(unsent)
        print(f"[RECOVERY] Found {total} stored messages")
        print("[RECOVERY] Sending stored messages...\n")

        sent_ids = []
        count = 0

        for msg_id, topic, message in unsent:

            if not (self.connected and self.client.is_connected()):
                print("[RECOVERY] Connection lost during recovery")
                break

            payload = self._create_payload(msg_id, topic, message)

            result = self.client.publish(topic, payload, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                sent_ids.append(msg_id)
                count += 1
                self.total_sent += 1

                #SMART PROGRESS LOG
                if count % 500 == 0:
                    percent = (count / total) * 100
                    print(f"[RECOVERY] {count}/{total} ({percent:.1f}%) completed")

            else:
                print(f"[ERROR] Failed {msg_id}")

            time.sleep(0.01)

        for msg_id in sent_ids:
            self.store.mark_sent(msg_id)

        self.store.cleanup_sent()

        print(f"\n[RECOVERY COMPLETE] {count} messages processed")
        print("[SYSTEM] Switching to LIVE data flow\n")

        self.recovering = False

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"\n[MQTT] Disconnected (code: {reason_code})")
        print("[MQTT] Waiting for automatic reconnect...")

        self.connected = False
