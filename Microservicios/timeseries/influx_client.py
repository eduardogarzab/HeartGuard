"""InfluxDB client helpers for the timeseries service."""
import os
from datetime import datetime
from typing import Dict, List, Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "heartguard-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "heartguard-metrics")
INFLUX_INTERNAL_URL = os.getenv("INFLUX_INTERNAL_URL", "http://influxdb:8086")

_client: Optional[InfluxDBClient] = None


def get_client() -> InfluxDBClient:
    global _client
    if _client is None:
        _client = InfluxDBClient(url=INFLUX_INTERNAL_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, timeout=10_000)
    return _client


def write_point(measurement: str, tags: Dict[str, str], fields: Dict, timestamp: str) -> None:
    client = get_client()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    point = Point(measurement)
    for key, value in tags.items():
        point = point.tag(key, str(value))
    for key, value in fields.items():
        point = point.field(key, value)
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        point = point.time(dt)
    except ValueError:
        pass
    write_api.write(bucket=INFLUX_BUCKET, record=point)


def write_line_protocol(payload: str) -> None:
    client = get_client()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=INFLUX_BUCKET, record=payload)


def query_aggregated(
    measurement: str,
    user_id: str,
    start: str,
    end: str,
    window: str,
    agg: str,
    limit: int,
    page: int,
) -> List[Dict]:
    client = get_client()
    query_api = client.query_api()
    offset = (page - 1) * limit
    flux = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: {start}, stop: {end})
  |> filter(fn: (r) => r["_measurement"] == "{measurement}")
  |> filter(fn: (r) => r["user_id"] == "{user_id}")
  |> aggregateWindow(every: {window}, fn: {agg}, createEmpty: false)
  |> sort(columns: ["_time"])
  |> limit(n: {limit}, offset: {offset})
'''
    tables = query_api.query(flux)
    results: Dict[str, Dict] = {}
    for table in tables:
        for record in table.records:
            time_key = record.get_time().isoformat()
            entry = results.setdefault(time_key, {"time": time_key})
            field_name = f"{record.get_field()}_{agg}"
            entry[field_name] = record.get_value()
    ordered = [results[key] for key in sorted(results.keys())]
    return ordered


def ping() -> bool:
    try:
        return bool(get_client().ping())
    except Exception:
        return False
