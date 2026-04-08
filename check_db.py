import json
import os

STORE_FILE = "sensor_store.json"

if not os.path.exists(STORE_FILE):
    print("No sensor_store.json found.")
    exit()

try:
    with open(STORE_FILE, "r") as f:
        content = f.read().strip()

        if not content:
            print("Store file is empty. System may still be writing.")
            exit()

        readings = json.loads(content)

except json.JSONDecodeError:
    print("Store file is being written. Try again in a moment.")
    exit()


total  = len(readings)
sent   = sum(1 for r in readings if r["sent"])
unsent = total - sent

print("========== STORE SUMMARY ==========")
print(f"Total readings : {total}")
print(f"Sent to broker : {sent}")
print(f"Unsent (saved) : {unsent}")

print("\n========== LATEST 10 READINGS ==========")
for r in readings[-10:][::-1]:
    status = "sent" if r["sent"] else "NOT SENT"
    print(f"{r['id']} | {r['topic']} -> {r['message']} ({status})")
