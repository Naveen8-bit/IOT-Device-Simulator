import random

class Sensor:
    def read_temperature(self):
        if random.random() < 0.01:
            raise Exception("Temperature sensor failure")
        return random.randint(20, 40)

    def read_humidity(self):
        if random.random() < 0.01:
            raise Exception("Humidity sensor failure")
        return random.randint(40, 80)

    def get_status(self):
        return random.choice(["OK", "WARN", "FAIL"])
