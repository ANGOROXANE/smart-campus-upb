# Backend Smart Campus UPB

Backend BD-GL 1 construit avec FastAPI, MongoDB, InfluxDB, Redis/Sentinel, Nginx, JWT/RBAC, cache-aside, Pub/Sub, rate limiting, ingestion Node-RED/MQTT et metriques Prometheus.

## Architecture

Client -> Nginx -> backend-1/backend-2/backend-3 -> MongoDB, InfluxDB, Redis via Sentinel.

Le code est separe en couches :

- `app/api` : routes HTTP.
- `app/models` : schemas Pydantic.
- `app/repositories` : acces MongoDB.
- `app/services` : logique metier, cache, Pub/Sub, metrics, rate limiting.
- `app/db` : clients MongoDB, InfluxDB, Redis/Sentinel.
- `app/core` : configuration, logging, securite, exceptions.

## Variables d'environnement

Copier `.env.example` vers `.env` pour Docker Compose.

- `MONGO_URI`, `MONGO_DATABASE`
- `INFLUX_URL`, `INFLUX_TOKEN`, `INFLUX_ORG`, `INFLUX_BUCKET`
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `REDIS_URL` pour usage local simple
- `REDIS_SENTINEL_HOSTS`, `REDIS_SENTINEL_SERVICE`, `REDIS_DB`
- `CACHE_TTL_SECONDS`, `LATEST_MEASUREMENTS_CACHE_TTL_SECONDS`
- `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`
- `NODE_RED_API_KEY`
- `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` pour creer un administrateur au demarrage si absent
- `APP_HOST`, `APP_PORT`, `LOG_LEVEL`, `INSTANCE_ID`

Aucun secret ne doit etre stocke en clair dans Git. `.env` est ignore dans `backend/.gitignore`.

## Lancement local

```powershell
cd backend
python -m pip install -r requirements.txt
$env:JWT_SECRET="dev-secret-with-at-least-32-characters"
$env:NODE_RED_API_KEY="dev-node-red-key"
python -m uvicorn app.main:app --reload
```

Swagger : `http://127.0.0.1:8000/docs`

## Docker Compose

```powershell
cd backend
copy .env.example .env
docker compose up -d --build
docker compose ps
```

Services :

- `nginx` : reverse proxy expose sur `${NGINX_PORT:-8000}`.
- `backend-1`, `backend-2`, `backend-3` : instances FastAPI.
- `mongodb` : base documentaire.
- `influxdb` : series temporelles.
- `redis-master`, `redis-replica-1`, `redis-replica-2`.
- `redis-sentinel-1`, `redis-sentinel-2`, `redis-sentinel-3`.

Le backend utilise Sentinel via `REDIS_SENTINEL_HOSTS` pour decouvrir le master Redis.

## Endpoints principaux

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /rooms`
- `POST /rooms` admin requis
- `GET /sensors`
- `POST /sensors` admin requis
- `POST /measurements`
- `GET /measurements/latest`
- `GET /measurements/history`
- `POST /ingestion/measurements`
- `GET /metrics`

## MongoDB

Collections prevues :

- `users` : `email`, `password_hash`, `role`, `is_active`
- `rooms` : `name`, `building`, `floor`, `capacity`
- `sensors` : `name`, `sensor_type`, `room`, `unit`
- `events` : preparee pour les phases d'evenements

Index crees au demarrage quand MongoDB est joignable :

- `users_email_unique`
- `rooms_name_unique`
- `sensors_room_name_unique`
- `events_created_at`

## InfluxDB

Measurement : `campus_measurements`.

Tags :

- `room`
- `sensor`

Fields :

- `temperature`
- `presence`

Timestamp : `timestamp`.

Une mesure `salle + temperature + presence + timestamp` est transformee en point InfluxDB avec `room` et `sensor` en tags, puis `temperature` et `presence` en fields.

## Redis, cache et Pub/Sub

Cache-aside :

- `GET /rooms` utilise `rooms:list:v1`.
- `GET /sensors` utilise `sensors:list:v1`.
- `GET /measurements/latest` utilise `measurements:latest:{limit}:v1`.

Les caches ont un TTL configurable. Les creations de salles/capteurs et les nouvelles mesures invalident les cles concernees. Les evenements Pub/Sub utilisent :

- `smart-campus:measurements`
- `smart-campus:rooms`
- `smart-campus:sensors`
- `smart-campus:events`

## Rate limiting

Le rate limiting utilise Redis pour partager les compteurs entre instances. Les limites sont configurees par `RATE_LIMIT_REQUESTS` et `RATE_LIMIT_WINDOW_SECONDS`. Un depassement retourne HTTP 429.

## Integration RIST / Node-RED

Le simulateur MQTT RIST peut conserver les topics existants :

- `campus/A101/data`
- `campus/A102/data`
- `campus/B201/data`

Node-RED doit convertir ou relayer la mesure vers :

```http
POST /ingestion/measurements
X-API-Key: ${NODE_RED_API_KEY}
Content-Type: application/json
```

Body accepte :

```json
{
  "salle": "A101",
  "temperature": 24.2,
  "presence": true,
  "timestamp": "2026-08-08T10:00:00Z"
}
```

`room` peut remplacer `salle`. Si `sensor` est absent, le backend utilise `node-red`.

## Contrat BD-GL 2

BD-GL 2 peut consommer :

- `GET /rooms`
- `GET /sensors`
- `GET /measurements/latest`
- `GET /measurements/history`
- `GET /health/ready`

Les routes d'ecriture sensibles utilisent JWT/RBAC ou `NODE_RED_API_KEY`.

## Metriques

`GET /metrics` expose les metriques Prometheus :

- `smart_campus_http_requests_total`
- `smart_campus_http_request_duration_seconds`
- `smart_campus_http_errors_total`
- `smart_campus_dependency_up`

## Tests

```powershell
cd backend
python -m pytest
python -m pytest --cov=app --cov-report=term-missing
```

Objectif atteint lors de la validation : couverture superieure a 70 %.

## Validation Sentinel

Test manuel de failover :

```powershell
docker compose stop redis-master
docker compose exec redis-sentinel-1 redis-cli -p 26379 sentinel get-master-addr-by-name smart-campus-redis
docker compose ps
```

Le backend doit continuer a utiliser Redis via Sentinel apres promotion d'un replica.

## Depannage

- Si `/health/ready` indique `redis: down`, verifier les Sentinels et le master promu.
- Si `/health/ready` indique `influxdb: down`, verifier `INFLUX_TOKEN`, `INFLUX_ORG` et `INFLUX_BUCKET`.
- Si `/auth/login` retourne 503, verifier `JWT_SECRET`.
- Si l'ingestion retourne 401, verifier `NODE_RED_API_KEY`.
