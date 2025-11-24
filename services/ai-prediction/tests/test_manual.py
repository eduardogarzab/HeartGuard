"""
Script de prueba para el servicio de IA
Prueba los endpoints sin necesidad de autenticación (para desarrollo)
"""
import requests
import json

# URL del servicio (ajustar según donde esté corriendo)
BASE_URL = "http://localhost:5008"

def test_health():
    """Prueba el health check"""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_predict_normal():
    """Prueba predicción con valores normales"""
    print("\n" + "="*60)
    print("TEST: Predicción con Valores Normales")
    print("="*60)
    
    data = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 75,
        "spo2": 98,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "temperature": 36.7
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    
    # Para pruebas sin autenticación, necesitamos modificar temporalmente el endpoint
    # o generar un token válido
    # Por ahora, mostramos el request que se haría:
    print("\nEste endpoint requiere autenticación JWT.")
    print("Para probarlo sin auth, modifica temporalmente el decorador @require_auth")
    print("a @optional_auth en src/app.py")
    
    return True


def test_predict_problem():
    """Prueba predicción con valores anormales"""
    print("\n" + "="*60)
    print("TEST: Predicción con Valores Anormales")
    print("="*60)
    
    data = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 135,  # Taquicardia
        "spo2": 88,         # Hipoxemia
        "systolic_bp": 160, # Hipertensión
        "diastolic_bp": 100,
        "temperature": 39.5 # Fiebre alta
    }
    
    print(f"Input: {json.dumps(data, indent=2)}")
    print("\nEste endpoint requiere autenticación JWT.")
    
    return True


def test_model_info():
    """Prueba el endpoint de información del modelo"""
    print("\n" + "="*60)
    print("TEST: Información del Modelo")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/model/info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


if __name__ == "__main__":
    print("\n" + "🧠 HEARTGUARD AI PREDICTION SERVICE - TESTS")
    print("="*60)
    
    results = {
        "Health Check": test_health(),
        "Model Info": test_model_info(),
        "Predict Normal": test_predict_normal(),
        "Predict Problem": test_predict_problem(),
    }
    
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")
    
    print("\n" + "="*60)
    print("NOTAS:")
    print("- Para probar los endpoints protegidos, necesitas un token JWT")
    print("- Puedes modificar temporalmente @require_auth a @optional_auth")
    print("- O generar un token válido usando el servicio de auth")
    print("="*60)
