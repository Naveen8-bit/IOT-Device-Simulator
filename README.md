IoT Device Simulator

This project is a Python-based IoT device simulator that mimics real-world sensor behavior by generating temperature, humidity, and status data from multiple virtual sensors running in parallel. The data is sent to an MQTT broker using a queue-based publishing system, ensuring efficient and scalable communication. It also handles network failures gracefully by storing data locally in a JSON file and automatically forwarding it once the connection is restored. The system is designed with thread safety, logging, and configuration support to closely resemble a real IoT environment.

This project demonstrates practical concepts like MQTT communication, multithreading, fault tolerance, and reliable data handling, making it a strong foundation for real-world IoT applications.
