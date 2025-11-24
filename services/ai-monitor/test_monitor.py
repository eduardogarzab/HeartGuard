#!/usr/bin/env python3
"""
Test script para AI Monitor Service

Este script simula el flujo completo sin necesidad de tener
InfluxDB, PostgreSQL o servicios externos corriendo.
"""

import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_influx_client():
    """Test del cliente InfluxDB (mock)"""
    logger.info("=" * 60)
    logger.info("TEST: InfluxDB Client")
    logger.info("=" * 60)
    
    # Simular datos de InfluxDB
    mock_vital_signs = {
        "patient_id": "abc-123-def-456",
        "timestamp": datetime.utcnow().isoformat(),
        "heart_rate": 135,
        "spo2": 88,
        "systolic_bp": 160,
        "diastolic_bp": 100,
        "temperature": 39.5,
        "gps_latitude": 19.4326,
        "gps_longitude": -99.1332
    }
    
    logger.info(f"✓ Mock vital signs retrieved for patient {mock_vital_signs['patient_id']}")
    logger.info(f"  - Heart Rate: {mock_vital_signs['heart_rate']} bpm")
    logger.info(f"  - SpO2: {mock_vital_signs['spo2']}%")
    logger.info(f"  - Blood Pressure: {mock_vital_signs['systolic_bp']}/{mock_vital_signs['diastolic_bp']} mmHg")
    logger.info(f"  - Temperature: {mock_vital_signs['temperature']}°C")
    
    return mock_vital_signs


def test_ai_prediction(vital_signs):
    """Test del servicio de IA (mock)"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST: AI Prediction Service")
    logger.info("=" * 60)
    
    # Simular respuesta del modelo de IA
    mock_prediction = {
        "prediction": 1,
        "probability": 0.95,
        "risk_level": "HIGH",
        "alerts": [
            {
                "type": "ARRHYTHMIA",
                "severity": "high",
                "message": "Frecuencia cardíaca elevada: 135 bpm",
                "value": 135,
                "unit": "bpm"
            },
            {
                "type": "DESAT",
                "severity": "critical",
                "message": "Saturación de oxígeno baja: 88%",
                "value": 88,
                "unit": "%"
            },
            {
                "type": "HYPERTENSION",
                "severity": "high",
                "message": "Presión arterial elevada: 160/100 mmHg",
                "value": "160/100",
                "unit": "mmHg"
            },
            {
                "type": "FEVER",
                "severity": "medium",
                "message": "Temperatura corporal elevada: 39.5°C",
                "value": 39.5,
                "unit": "°C"
            }
        ],
        "timestamp": vital_signs["timestamp"],
        "patient_id": vital_signs["patient_id"],
        "gps_latitude": vital_signs["gps_latitude"],
        "gps_longitude": vital_signs["gps_longitude"]
    }
    
    logger.info(f"✓ Prediction received")
    logger.info(f"  - Problem detected: {'YES' if mock_prediction['prediction'] == 1 else 'NO'}")
    logger.info(f"  - Probability: {mock_prediction['probability']:.1%}")
    logger.info(f"  - Risk Level: {mock_prediction['risk_level']}")
    logger.info(f"  - Alerts detected: {len(mock_prediction['alerts'])}")
    
    for i, alert in enumerate(mock_prediction['alerts'], 1):
        logger.info(f"    {i}. {alert['type']} ({alert['severity']}): {alert['message']}")
    
    return mock_prediction


def test_alert_creation(prediction):
    """Test de creación de alertas (mock)"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST: Alert Creation in PostgreSQL")
    logger.info("=" * 60)
    
    created_alerts = []
    
    for alert in prediction['alerts']:
        alert_id = f"alert-{alert['type'].lower()}-{datetime.utcnow().timestamp()}"
        
        logger.info(f"✓ Alert created: {alert_id}")
        logger.info(f"  - Type: {alert['type']}")
        logger.info(f"  - Severity: {alert['severity']}")
        logger.info(f"  - Patient: {prediction['patient_id']}")
        logger.info(f"  - Location: ({prediction['gps_latitude']}, {prediction['gps_longitude']})")
        
        created_alerts.append({
            "alert_id": alert_id,
            "type": alert['type'],
            "severity": alert['severity'],
            "message": alert['message']
        })
    
    return created_alerts


def test_caregiver_notification(patient_id, alerts):
    """Test de notificaciones (mock)"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST: Caregiver Notifications")
    logger.info("=" * 60)
    
    # Simular caregivers
    mock_caregivers = [
        {
            "user_id": "caregiver-1",
            "name": "Dr. Juan Pérez",
            "email": "juan.perez@hospital.com",
            "phone": "+52 55 1234 5678",
            "notify_email": True,
            "notify_sms": True,
            "notify_push": False
        },
        {
            "user_id": "caregiver-2",
            "name": "Enf. María González",
            "email": "maria.gonzalez@hospital.com",
            "phone": "+52 55 8765 4321",
            "notify_email": True,
            "notify_sms": False,
            "notify_push": True
        }
    ]
    
    logger.info(f"Found {len(mock_caregivers)} caregivers for patient {patient_id}")
    
    notifications_sent = 0
    
    for caregiver in mock_caregivers:
        logger.info(f"\n  Notifying: {caregiver['name']}")
        
        if caregiver['notify_email']:
            logger.info(f"    ✓ Email sent to {caregiver['email']}")
            notifications_sent += 1
        
        if caregiver['notify_sms']:
            logger.info(f"    ✓ SMS sent to {caregiver['phone']}")
            notifications_sent += 1
        
        if caregiver['notify_push']:
            logger.info(f"    ✓ Push notification sent")
            notifications_sent += 1
    
    logger.info(f"\n✓ Total notifications sent: {notifications_sent}")
    
    return notifications_sent


def test_full_workflow():
    """Test del flujo completo"""
    logger.info("\n\n")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 10 + "AI MONITOR SERVICE - FULL WORKFLOW TEST" + " " * 8 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")
    
    try:
        # 1. Obtener signos vitales
        vital_signs = test_influx_client()
        
        # 2. Predecir con IA
        prediction = test_ai_prediction(vital_signs)
        
        # 3. Crear alertas
        if prediction['prediction'] == 1:
            alerts = test_alert_creation(prediction)
            
            # 4. Notificar caregivers
            notifications = test_caregiver_notification(
                prediction['patient_id'],
                alerts
            )
        else:
            logger.info("\n✓ No health problems detected - No alerts created")
            alerts = []
            notifications = 0
        
        # Resumen
        logger.info("")
        logger.info("=" * 60)
        logger.info("WORKFLOW SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✓ Vital signs retrieved: 1")
        logger.info(f"✓ Predictions made: 1")
        logger.info(f"✓ Alerts created: {len(alerts)}")
        logger.info(f"✓ Notifications sent: {notifications}")
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
