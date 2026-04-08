import paho.mqtt.client as mqtt
import json

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "farm/sensors/Naveen_101sensor/#"

seen_ids = set()

def on_connect(client, userdata, flags, reason_code, properties):
    print("[Subscriber] Connected\n")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode()
        data = json.loads(raw)

        msg_id    = data["id"]
        sensor_id = data["sensor_id"]
        data_type = data["type"]
        value     = data["value"]

        # Skip duplicates (QoS 1)
        if msg_id in seen_ids:
            return
        seen_ids.add(msg_id)

        print("----------- MESSAGE -----------")
        print(f"Sensor : {sensor_id}")
        print(f"Type   : {data_type}")
        print(f"Value  : {value}")
        print(f"Msg ID : {msg_id}")
        print("--------------------------------\n")

    except Exception as e:
        print("[ERROR]", e)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_forever()
