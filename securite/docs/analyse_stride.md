# Analyse STRIDE — Smart Campus UPB

| Menace | Composant | Description | Preuve/Impact | Contre-mesure |
|---|---|---|---|---|
| Spoofing | Broker MQTT | Un attaquant peut se faire passer pour un capteur légitime et publier de fausses données | Démontré par l'attaque replay (message rejoué avec ancien timestamp) | Authentification par certificat client (mutual TLS) |
| Tampering | Communication MQTT | Modification d'un message en transit | Démontré par l'attaque MITM (température 27°C falsifiée en 75°C) | TLS activé sur le broker (port 8883) - fait |
| Repudiation | API Backend | Absence de logs détaillés liant chaque action à un utilisateur identifié | À vérifier avec l'équipe backend | Logging des requêtes avec horodatage, IP et identifiant utilisateur |
| Information disclosure | Broker MQTT (avant sécurisation) | Données capteurs lisibles en clair sur le réseau | Démontré par capture Wireshark (sniffing MQTT port 1883) | TLS activé sur le broker - fait |
| Denial of service | API Backend (/auth/login) | Absence de blocage après tentatives de connexion répétées | Démontré par 5 tentatives de brute force consécutives sans blocage (toutes en 401) | Renforcer le rate limiting spécifiquement sur les routes d'authentification |
| Elevation of privilege | API Backend (/measurements/latest) | Accès aux données de mesure sans authentification | Démontré par requête curl sans token, réponse HTTP 200 | Exiger un token JWT valide sur toutes les routes de données |
