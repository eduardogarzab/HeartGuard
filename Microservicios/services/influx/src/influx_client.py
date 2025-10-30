import os
from datetime import datetime
from typing import List, Dict, Any

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.buckets_api import BucketsApi

INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG", "heartguard")
DEFAULT_BUCKET = os.getenv("influx_DEFAULT_BUCKET", os.getenv("INFLUX_BUCKET", "default"))

_client = None


def get_client() -> InfluxDBClient:
    global _client
    if _client is None:
        _client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    return _client


def write_points(bucket: str, points: List[Dict[str, Any]]):
    client = get_client()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    records = []
    for point in points:
        measurement = point.get("measurement")
        tags = point.get("tags", {})
        fields = point.get("fields", {})
        timestamp = point.get("timestamp")
        p = Point(measurement)
        for key, value in tags.items():
            p = p.tag(key, value)
        for key, value in fields.items():
            p = p.field(key, value)
        if timestamp:
            p = p.time(datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
        records.append(p)
    write_api.write(bucket=bucket or DEFAULT_BUCKET, org=INFLUX_ORG, record=records)


def query_data(flux_query: str):
    client = get_client()
    query_api = client.query_api()
    tables = query_api.query(flux_query, org=INFLUX_ORG)
    results = []
    for table in tables:
        for record in table:
            results.append({
                "measurement": record.get_measurement(),
                "time": record.get_time().isoformat() if record.get_time() else None,
                "fields": record.values
            })
    return results


def query_aggregate(bucket: str, measurement: str, start: str, stop: str, window: str, aggregate: str):
    flux = f"from(bucket: \"{bucket}\") |> range(start: {start}, stop: {stop}) |> filter(fn: (r) => r._measurement == \"{measurement}\")"
    if aggregate:
        flux += f" |> aggregateWindow(every: {window}, fn: {aggregate}, createEmpty: false)"
    return query_data(flux)


def list_buckets():
    client = get_client()
    api: BucketsApi = client.buckets_api()
    buckets = api.find_buckets().buckets
    return buckets


def create_bucket(name: str, retention_seconds: int = 0):
    client = get_client()
    api: BucketsApi = client.buckets_api()
    return api.create_bucket(bucket_name=name, org=INFLUX_ORG, retention_rules=[] if retention_seconds == 0 else [{"type": "expire", "every_seconds": retention_seconds}])


def delete_bucket(bucket_id: str):
    client = get_client()
    api: BucketsApi = client.buckets_api()
    api.delete_bucket(bucket_id)
