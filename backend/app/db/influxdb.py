from influxdb_client import InfluxDBClient

from app.core.config import Settings


def create_influx_client(settings: Settings) -> InfluxDBClient:
    token = settings.influx_token.get_secret_value() if settings.influx_token else ""
    return InfluxDBClient(
        url=settings.influx_url,
        token=token,
        org=settings.influx_org,
        timeout=2000,
    )
