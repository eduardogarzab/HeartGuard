# signal_service/app/repository/stream_repository.py
from ..database import SessionLocal
from ..models.models import SignalStream, TimeseriesData

def create_stream(org_id: str, patient_id: int, device_key_id: int, stream_type: str):
    """
    Creates a new signal stream in the database.
    """
    db = SessionLocal()
    try:
        new_stream = SignalStream(
            org_id=org_id,
            patient_id=patient_id,
            device_key_id=device_key_id,
            stream_type=stream_type
        )
        db.add(new_stream)
        db.commit()
        db.refresh(new_stream)
        return new_stream
    finally:
        db.close()

def find_streams_by_patient(patient_id: int):
    """
    Finds all streams associated with a given patient ID.
    """
    db = SessionLocal()
    try:
        return db.query(SignalStream).filter(SignalStream.patient_id == patient_id).all()
    finally:
        db.close()

def batch_insert_timeseries_data(data_list: list):
    """
    Performs a bulk insert of timeseries data.
    This is optimized for high-throughput writes from the worker.

    Args:
        data_list: A list of dictionaries, where each dict contains
                   'timestamp', 'stream_id', and 'value'.
    """
    if not data_list:
        return

    db = SessionLocal()
    try:
        # bulk_insert_mappings is efficient for inserting many rows.
        db.bulk_insert_mappings(TimeseriesData, data_list)
        db.commit()
    except Exception as e:
        db.rollback()
        # In a real app, you would log this error and potentially move
        # the failed batch to a dead-letter queue.
        print(f"Error during batch insert: {e}")
    finally:
        db.close()
