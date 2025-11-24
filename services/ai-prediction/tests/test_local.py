#!/usr/bin/env python3
"""
Script de prueba rápida del servicio de IA
Ejecuta una predicción de ejemplo sin necesidad de autenticación
"""
import sys
import os
import json

# Agregar el directorio padre al path para imports absolutos
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.ml.model_loader import ModelLoader
from src.ml.predictor import HealthPredictor
from src.config import MODEL_PATH


def test_model_loading():
    """Prueba la carga del modelo"""
    print("\n" + "="*60)
    print("TEST 1: Cargar Modelo")
    print("="*60)
    
    loader = ModelLoader()
    
    try:
        model = loader.load_model(MODEL_PATH)
        print(f"✅ Modelo cargado exitosamente")
        
        info = loader.get_model_info()
        print(f"\nInformación del modelo:")
        print(f"  - Tipo: {info['model_type']}")
        print(f"  - Estimadores: {info['n_estimators']}")
        print(f"  - Features: {info['n_features']}")
        print(f"  - Max Depth: {info['max_depth']}")
        
        return True
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return False


def test_prediction_normal():
    """Prueba predicción con valores normales"""
    print("\n" + "="*60)
    print("TEST 2: Predicción con Valores Normales")
    print("="*60)
    
    predictor = HealthPredictor()
    
    # Valores normales de signos vitales
    vital_signs = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 75,
        "spo2": 98,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "temperature": 36.7
    }
    
    print(f"Input: {json.dumps(vital_signs, indent=2)}")
    
    try:
        result = predictor.predict(vital_signs, threshold=0.6)
        
        print(f"\n✅ Predicción exitosa:")
        print(f"  - Has Problem: {result['has_problem']}")
        print(f"  - Probability: {result['probability']:.4f} ({result['probability']*100:.1f}%)")
        print(f"  - Alerts: {len(result['alerts'])}")
        
        if result['alerts']:
            print(f"\n  Alertas detectadas:")
            for alert in result['alerts']:
                print(f"    • {alert['type']}: {alert['message']} (Severidad: {alert['severity']})")
        else:
            print(f"  ✓ Sin alertas - Valores normales")
        
        return True
    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_abnormal():
    """Prueba predicción con valores anormales"""
    print("\n" + "="*60)
    print("TEST 3: Predicción con Valores Anormales")
    print("="*60)
    
    predictor = HealthPredictor()
    
    # Valores anormales
    vital_signs = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 135,  # Taquicardia
        "spo2": 88,         # Hipoxemia
        "systolic_bp": 160, # Hipertensión
        "diastolic_bp": 100,
        "temperature": 39.5 # Fiebre alta
    }
    
    print(f"Input: {json.dumps(vital_signs, indent=2)}")
    
    try:
        result = predictor.predict(vital_signs, threshold=0.6)
        
        print(f"\n✅ Predicción exitosa:")
        print(f"  - Has Problem: {result['has_problem']}")
        print(f"  - Probability: {result['probability']:.4f} ({result['probability']*100:.1f}%)")
        print(f"  - Alerts: {len(result['alerts'])}")
        
        if result['alerts']:
            print(f"\n  Alertas detectadas:")
            for alert in result['alerts']:
                value_str = ""
                if 'value' in alert and alert['value'] is not None:
                    unit = alert.get('unit', '')
                    value_str = f" (Valor: {alert['value']} {unit})"
                print(f"    • {alert['type']}: {alert['message']}{value_str}")
                print(f"      Severidad: {alert['severity'].upper()}")
        
        return True
    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_prediction():
    """Prueba predicción en lote"""
    print("\n" + "="*60)
    print("TEST 4: Predicción en Lote")
    print("="*60)
    
    predictor = HealthPredictor()
    
    readings = [
        {
            "gps_longitude": -99.1332,
            "gps_latitude": 19.4326,
            "heart_rate": 75,
            "spo2": 98,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "temperature": 36.7,
            "timestamp": "2025-11-23T21:59:00Z"
        },
        {
            "gps_longitude": -99.1332,
            "gps_latitude": 19.4326,
            "heart_rate": 135,
            "spo2": 88,
            "systolic_bp": 160,
            "diastolic_bp": 100,
            "temperature": 39.5,
            "timestamp": "2025-11-23T22:00:00Z"
        },
        {
            "gps_longitude": -99.1332,
            "gps_latitude": 19.4326,
            "heart_rate": 70,
            "spo2": 97,
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "temperature": 36.5,
            "timestamp": "2025-11-23T22:01:00Z"
        }
    ]
    
    print(f"Procesando {len(readings)} lecturas...")
    
    try:
        result = predictor.batch_predict(readings, threshold=0.6)
        
        print(f"\n✅ Predicción en lote exitosa:")
        print(f"\nResumen:")
        print(f"  - Total lecturas: {result['summary']['total']}")
        print(f"  - Problemas detectados: {result['summary']['problems_detected']}")
        print(f"  - Probabilidad promedio: {result['summary']['avg_probability']:.4f}")
        
        print(f"\nDetalle por lectura:")
        for i, pred in enumerate(result['predictions'], 1):
            timestamp = pred.get('timestamp', 'N/A')
            has_problem = pred.get('has_problem', False)
            probability = pred.get('probability', 0.0)
            alerts_count = len(pred.get('alerts', []))
            
            status = "⚠️ PROBLEMA" if has_problem else "✓ Normal"
            print(f"  {i}. {timestamp}: {status} (Prob: {probability:.2f}, Alertas: {alerts_count})")
        
        return True
    except Exception as e:
        print(f"❌ Error en predicción en lote: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🧠 HEARTGUARD AI PREDICTION SERVICE - TESTS LOCALES")
    print("="*60)
    print("Estos tests prueban el modelo ML directamente")
    print("No requieren que el servicio Flask esté corriendo")
    print("="*60)
    
    results = {}
    
    # Test 1: Cargar modelo
    results["Cargar Modelo"] = test_model_loading()
    
    if results["Cargar Modelo"]:
        # Solo continuar si el modelo se cargó
        results["Predicción Normal"] = test_prediction_normal()
        results["Predicción Anormal"] = test_prediction_abnormal()
        results["Predicción en Lote"] = test_batch_prediction()
    else:
        print("\n❌ No se puede continuar sin modelo cargado")
        print("Por favor, asegúrate de que el archivo modelo_salud_randomforest.pkl")
        print("esté en la carpeta models/")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("El servicio de IA está listo para ser usado")
    else:
        print("⚠️ Algunos tests fallaron")
        print("Revisa los errores arriba")
    print("="*60)
    
    sys.exit(0 if all_passed else 1)
