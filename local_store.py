import json
import os
import threading
import time

STORE_FILE = "sensor_store.json"
MAX_RECORDS = 5000   # limit storage size


class LocalStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.readings = []

        if os.path.exists(STORE_FILE):
            try:
                with open(STORE_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        self.readings = json.loads(content)
            except json.JSONDecodeError:
                print("[LocalStore] Corrupted file. Starting fresh.")
                self.readings = []

        print(f"[LocalStore] Loaded {len(self.readings)} records")

# safe
    def _save(self):
        temp_file = STORE_FILE + ".tmp"

        # Write to temp file
        with open(temp_file, "w") as f:
            json.dump(self.readings, f)
            f.flush()              
            os.fsync(f.fileno())   

        # Retry replace
        for _ in range(3):
            try:
                os.replace(temp_file, STORE_FILE)
                return
            except PermissionError:
                time.sleep(0.05)  

        print("[LocalStore] ERROR: Failed to replace file after retries")

    # save with limit protection
    def save(self, msg_id, topic, message):
        with self.lock:
            if len(self.readings) >= MAX_RECORDS:
                print("[WARNING] Store full. Dropping oldest data.")
                self.readings.pop(0)

            self.readings.append({
                "id": msg_id,
                "topic": topic,
                "message": message,
                "sent": False
            })

            self._save()

    def get_unsent(self):
        with self.lock:
            unsent = [(r["id"], r["topic"], r["message"])
                      for r in self.readings if not r["sent"]]

        print(f"[LocalStore] Unsent messages: {len(unsent)}")
        return unsent

    def mark_sent(self, msg_id):
        with self.lock:
            for r in self.readings:
                if r["id"] == msg_id:
                    r["sent"] = True
                    break
            self._save()

    # cleanup after sending
    def cleanup_sent(self):
        with self.lock:
            before = len(self.readings)
            self.readings = [r for r in self.readings if not r["sent"]]
            after = len(self.readings)

            self._save()
            print(f"[LocalStore] Cleanup: {before - after} removed, {after} remaining")

    def stats(self):
        total = len(self.readings)
        sent = sum(1 for r in self.readings if r["sent"])
        unsent = total - sent

        print("\n[LocalStore] ===== STATS =====")
        print(f"Total  : {total}")
        print(f"Sent   : {sent}")
        print(f"Unsent : {unsent}")
        print("=============================\n")
