import random
class TemperatureSensor:
    def read_temperature(self):
        if random.random() < 0.1:
            raise Exception("Sensor failure")
        return random.randint(10, 43)
