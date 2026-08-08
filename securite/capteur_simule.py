import paho.mqtt.client as mqtt
import json
import time
import random

client = mqtt.Client()
client.tls_set(ca_certs="securite/certs/ca.crt")
client.tls_insecure_set(True)
client.connect("localhost", 8883, 60)

salles = ["A101", "A102", "B201"]

while True:
    for salle in salles:
        data = {
            "salle": salle,
            "temperature": round(random.uniform(22, 28), 1),
            "presence": random.choice([True, False]),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        client.publish(f"campus/{salle}/data", json.dumps(data))
        print(f"Envoyé : {data}")
    time.sleep(5)